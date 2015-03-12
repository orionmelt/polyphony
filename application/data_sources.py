import re
import logging
import urllib2

import requests

from google.appengine.ext import ndb
from models import DataSource, TrackHost, Track, TrackMention
from track_hosts import YouTube, SoundCloud
from bs4 import BeautifulSoup

class CrawlError(Exception):
    pass

# Base class for data sources
class BaseDataSource(object):
    """
    A base class for data sources - such as reddit, blogs, etc.

    """

    def __init__(self, data_source):
        # DataSource model
        self.data_source = data_source
        self.youtube = YouTube()
        self.soundcloud = SoundCloud()

    def get_resource(self):
        pass

    def crawl(self):
        pass


class Reddit(BaseDataSource):
    """
    A class for data source reddit.

    """

    HEADERS = {"User-Agent" : "Polyphony v0.1 by /u/orionmelt"}

    def __init__(self, data_source):
        super(Reddit, self).__init__(data_source)

    def get_resource(self):
        return requests.get(self.data_source.source_url, headers=self.HEADERS)

    def crawl(self):
        position = 0
        mentions = []
        tracks = []
        source_type = self.data_source.source_type

        resource = self.get_resource()
        if not resource:
            raise CrawlError

        resource_json = resource.json()
        for submission in resource_json["data"]["children"]:
            reddit_id = submission["data"]["id"]
            permalink = \
                "http://www.reddit.com"+submission["data"]["permalink"].lower()
            url = submission["data"]["url"]
            reddit_title = submission["data"]["title"].encode("ascii","ignore")
            domain = submission["data"]["domain"].lower()
            subreddit = submission["data"]["subreddit"]


            artist = None
            title = None

            # Now that we have the domain, let's see 
            # if it is a supported TrackHost.
            track_host = TrackHost.query(TrackHost.domains==domain).get()

            # TODO - Handle subdomains such as m.youtube.com

            if not track_host:
                continue

            # Let's see if we've already processed this mention.
            mention = TrackMention.get_by_id(source_type+"_"+reddit_id)
            if mention:
                # Yes we have, just update hotness score
                mention.hotness_score = position
                mentions.append(mention)
            else:
                # Parse mention title to extract artist and track title

                if subreddit.lower() in ["listentothis", "music"]:
                    reddit_title = reddit_title.replace("--", "-")
                    g = re.match(r"(.+) - ([^\[]+)", reddit_title).groups()
                    if not g:
                        # Title does not follow guidelines, skip this mention
                        continue
                    artist, title = g

                if track_host.key.id()=="youtube":
                    track_id = self.youtube.parse_track_id(url)
                    if not track_id:
                        continue
                    track = Track.get_by_id("youtube_"+track_id)
                    if not track:
                        track = self.youtube.get_track_by_url(url)
                        if not track:
                            continue
                        else:
                            if artist and title:
                                track.title = \
                                    artist.strip() + " - " + title.strip()
                            tracks.append(track)
                elif track_host.key.id()=="soundcloud":
                    track = self.soundcloud.get_track_by_url(url)
                    if not track:
                        continue
                    if not Track.get_by_id(track.key.id()):
                        if artist and title:
                            track.title = \
                                    artist.strip() + " - " + title.strip()
                        tracks.append(track)
                
                mention = TrackMention(
                    id = source_type+"_"+reddit_id,
                    data_source = self.data_source.key,
                    track = track.key,
                    mention_title = reddit_title,
                    mention_url = permalink,
                    hotness_score = position
                )
                mentions.append(mention)
            
            position = position + 1
        if tracks:
            ndb.put_multi(tracks)
        if mentions:
            ndb.put_multi(mentions)


class HypeMachine(BaseDataSource):
    """
    A class for data source HypeMachine.

    """

    def __init__(self, data_source):
        super(HypeMachine, self).__init__(data_source)

    def get_resource(self):
        return requests.get(self.data_source.source_url)

    def crawl(self):
        position = 0
        mentions = []
        tracks = []
        source_type = self.data_source.source_type

        resource = self.get_resource()

        if not resource:
            raise CrawlError

        resource_json = resource.json()

        for key in resource_json:
            if not key.isdigit():
                continue
            artist = resource_json[key]["artist"]
            title = resource_json[key]["title"]
            hypem_post_id = str(resource_json[key]["mediaid"])

            mention = TrackMention.get_by_id(source_type + "_" + hypem_post_id)
            if not mention:
                # Search for this track on SoundCloud
                track = self.soundcloud.search_tracks(artist, title)
                # If no results, search on YouTube
                if not track:
                    track = self.youtube.search_tracks(artist, title)
                # Well, let's give up
                if not track:
                    continue
                track.title = artist + " - " + title
                if not Track.get_by_id(track.key.id()):
                    tracks.append(track)
                mention = TrackMention(
                    id = source_type + "_" + hypem_post_id,
                    data_source = self.data_source.key,
                    track = track.key,
                    mention_title = resource_json[key]["sitename"],
                    mention_url = resource_json[key]["posturl"],
                    hotness_score = int(key)
                )
                mentions.append(mention)
        
        if tracks:
            ndb.put_multi(tracks)
        if mentions:
            ndb.put_multi(mentions)


class NPR(BaseDataSource):
    """
    A class for data source NPR.

    """

    def __init__(self, data_source):
        super(NPR, self).__init__(data_source)

    def get_resource(self):
        return requests.get(self.data_source.source_url)

    def crawl(self):
        position = 0
        mentions = []
        tracks = []
        source_type = self.data_source.source_type

        resource = self.get_resource()

        if not resource:
            raise CrawlError

        resource_xml = resource.content
        resource_soup = BeautifulSoup(resource_xml)

        for item in resource_soup.find_all("item"):
            item_title = item.title.contents[0]
            if "new mix" in item_title.lower():
                new_mix_post_url = item.guid.contents[0]
                new_mix_post = BeautifulSoup(
                    requests.get(new_mix_post_url).content
                )
                for playlist_item in new_mix_post.find_all(
                        "article", 
                        {"class" : "playlistitem"}
                    ):
                    post_id = playlist_item["id"]
                    artist = playlist_item.find("h4").a.contents[0].strip()
                    title = playlist_item.find(
                        "li", 
                        {"class" : "song"}
                    ).contents[1].strip()

                    mention = TrackMention.get_by_id(
                        source_type + "_" + post_id
                    )

                    if not mention:
                        # Search for this track on SoundCloud
                        track = self.soundcloud.search_tracks(artist, title)
                        # If no results, search on YouTube
                        if not track:
                            track = self.youtube.search_tracks(artist, title)
                        # Well, let's give up
                        if not track:
                            continue
                        track.title = artist + " - " + title
                        if not Track.get_by_id(track.key.id()):
                            tracks.append(track)
                        mention = TrackMention(
                            id = source_type + "_" + post_id,
                            data_source = self.data_source.key,
                            track = track.key,
                            mention_title = item_title,
                            mention_url = new_mix_post_url,
                            hotness_score = position
                        )
                        mentions.append(mention)
                        position += 1

        if tracks:
            ndb.put_multi(tracks)
        if mentions:
            ndb.put_multi(mentions)


class Pitchfork(BaseDataSource):
    """
    A class for data source Pitchfork.

    """

    def __init__(self, data_source):
        super(Pitchfork, self).__init__(data_source)
        self.re_item_title = re.compile(r"(.+)\:\s*(.+)")
        self.re_soundcloud_url = re.compile(
            r"(https*\:\/\/api\.soundcloud\.com/tracks\/\d+)"
        )

    def get_resource(self):
        return requests.get(self.data_source.source_url)

    def crawl(self):
        position = 0
        mentions = []
        tracks = []
        source_type = self.data_source.source_type

        resource = self.get_resource()

        if not resource:
            raise CrawlError

        resource_xml = resource.content
        resource_soup = BeautifulSoup(resource_xml)

        for item in resource_soup.find_all("item"):
            track = None
            item_title = item.title.contents[0].encode("ascii", "ignore")
            artist, title = self.re_item_title.match(item_title).groups()
            title = re.sub(r"\"","",title)
            description_soup = BeautifulSoup(item.description.contents[0])
            iframe = description_soup.find("iframe")
            if not iframe:
                continue
            iframe_source = urllib2.unquote(iframe["src"])

            if "soundcloud.com" in iframe_source.lower():
                soundcloud_url = \
                    self.re_soundcloud_url.findall(iframe_source)[0]
                if soundcloud_url:
                    track = self.soundcloud.get_track_by_url(soundcloud_url)
            elif "youtube.com" in iframe_source.lower():
                track = self.youtube.get_track_by_url(iframe_source)
            else:
                continue
            if not track:
                continue
            track.title = artist + " - " + title
            tracks.append(track)
            mention = TrackMention(
                id = source_type + "_" + item.guid.contents[0],
                data_source = self.data_source.key,
                track = track.key,
                mention_title = item_title,
                mention_url = item.guid.contents[0],
                hotness_score = position
            )
            mentions.append(mention)
            position += 1

        if tracks:
            ndb.put_multi(tracks)
        if mentions:
            ndb.put_multi(mentions)
