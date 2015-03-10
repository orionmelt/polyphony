import urllib2
import logging
import re
import difflib
from collections import namedtuple
from urlparse import urlparse, parse_qs

import requests
import soundcloud

from models import Track, TrackHost

# Base class for track hosts
class BaseTrackHost(object):
    """
    A base class for "track hosts" - such as SoundCloud, Youtube, etc.

    """

    def __init__(self, id):
        # TrackHost id
        self.id = id

    def parse_track_id(self, url):
        pass

    def get_track_by_id(self, track_id):
        pass

    def get_track_by_url(self, url):
        pass

    def search_tracks(self, artist, title):
        pass

class YouTube(BaseTrackHost):
    """
    A class for track host YouTube.

    """

    API_KEY = "AIzaSyAJ0em8O_2LVGBQhZAiDZnFZIPtDQw1j8Q"

    def __init__(self):
        super(YouTube, self).__init__("youtube")
        self.re_iso8601 = re.compile("PT(\d+M)*(\d+S)*")

    def parse_track_id(self, url):
        """
        Given a YouTube video URL, parses the URL and returns YouTube video ID.

        """
        query = urlparse(url)
        if query.hostname == 'youtu.be':
            return query.path[1:]
        if query.hostname in ('www.youtube.com', 'youtube.com'):
            if query.path == '/watch':
                p = parse_qs(query.query)
                return p['v'][0]
            if query.path[:7] == '/embed/':
                return query.path.split('/')[2]
            if query.path[:3] == '/v/':
                return query.path.split('/')[2]
        return None

    def get_track_by_id(self, track_id):
        return self.get_track_by_url(
            "http://www.youtube.com/watch?v=%s" % track_id
        )

    def get_track_by_url(self, url):
        """
        Given a YouTube video url, constructs and returns a Track object.

        """
        title = ""
        duration = 0
        track = None
        video_id = self.parse_track_id(url)
        logging.info(url)
        logging.info(video_id)
        
        if not video_id:
            return None
        request_url = "https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails&key=%s&id=%s" % (self.API_KEY,video_id)
        api_response = requests.get(request_url)
        api_response_json = api_response.json()

        # TODO - Error handling for rate-limiting, service unavailable, etc.

        if api_response_json["items"]:
            title = api_response_json["items"][0]["snippet"]["title"]
            duration = \
                api_response_json["items"][0]["contentDetails"]["duration"]
            iso8601_minutes, iso8601_seconds = self.re_iso8601.match(
                duration
            ).groups()

            minutes = int(iso8601_minutes[:-1]) if iso8601_minutes else 0
            seconds = int(iso8601_seconds[:-1]) if iso8601_seconds else 0

            track = Track(
                id = self.id + "_" + video_id,
                title = title,
                duration_secs = 60*minutes+seconds,
                track_host = TrackHost.get_by_id(self.id).key
            )

        return track

    def search_tracks(self, artist, title):
        """
        Given an artist and title, searches YouTube and returns 
        closest result as a Track object.

        """
        track = None
        api_response = requests.get("https://www.googleapis.com/youtube/v3/search?part=snippet&key=%s&q=%s" % (self.API_KEY,(artist + " " + title).replace(" ", "+")))
        api_response_json = api_response.json()
        if not api_response_json["items"]:
            return None
        track_titles = [x["snippet"]["title"] for x in api_response_json["items"] if x["id"]["kind"] == "youtube#video"]

        closest_titles = difflib.get_close_matches(
            artist + " " + title, 
            track_titles
        )
        logging.info(artist + " " + title)
        logging.info(track_titles)
        logging.info(closest_titles)
        if not closest_titles:
            return None
        closest_video = [
            x for x in api_response_json["items"] \
                if x["snippet"]["title"]==closest_titles[0]
        ][0]
        
        video_id = closest_video["id"]["videoId"]
        track = Track.get_by_id(self.id + "_" + video_id)
        if not track:
            track = self.get_track_by_url(
                "http://www.youtube.com/watch?v=%s" % video_id
            )
        return track

# We need this because results from SoundCloud could either be a 
# Resource object or a dictionary.
SoundCloudTrack = namedtuple("SoundCloudTrack", "id author title duration")

class SoundCloud(BaseTrackHost):
    """
    A class for track host SoundCloud.

    """

    CLIENT_ID = "d3012111d6ea13fa210b214f82b7be3a"

    def __init__(self):
        super(SoundCloud, self).__init__("soundcloud")
        self.client = soundcloud.Client(client_id=self.CLIENT_ID)

    def get_track_by_id(self, track_id):
        pass

    def get_track_by_url(self, url):
        """
        Given a SoundCloud url, constructs and returns a Track object.

        """
        track = None
        api_response = self.client.get('/resolve', url=url)
        soundcloud_track = None
        if api_response.kind == "track":
            author = ""
            try:
                author = api_response.author
            except AttributeError:
                author = api_response.user["username"]
            soundcloud_track = SoundCloudTrack(
                id = str(api_response.id), 
                author = author, 
                title = api_response.title, 
                duration = int(api_response.duration)/1000
            )
        elif api_response.kind == "playlist":
            author = ""
            try:
                author = api_response.tracks[0]["author"]
            except KeyError:
                author = api_response.tracks[0]["user"]["username"]
            soundcloud_track = SoundCloudTrack(
                id = str(api_response.tracks[0]["id"]),
                author = author, 
                title = api_response.tracks[0]["title"],
                duration = int(api_response.tracks[0]["duration"])/1000
            )

        if soundcloud_track:
            track = Track(
                id = self.id + "_" + soundcloud_track.id,
                #artist = None,
                title = \
                    soundcloud_track.author + " - " + soundcloud_track.title,
                duration_secs = soundcloud_track.duration,
                track_host = TrackHost.get_by_id(self.id).key
            )

        return track

    def search_tracks(self, artist, title):
        """
        Given an artist and title, searches SoundCloud and returns closest 
        result as a Track object.

        """
        track = None
        logging.info("Searching SoundCloud for %s___%s" % (artist,title))
        api_response = self.client.get(
            '/tracks', 
            q=artist+" "+title, 
            limit=3
        )
        logging.info("Search results from SoundCloud:")
        logging.info(api_response)

        track_titles = [(x.id, ((x.author if hasattr(x,"author") else None) or x.user["username"]) + " " + x.title) for x in api_response]
        closest_titles = difflib.get_close_matches(
            artist + " " + title, 
            [x[1] for x in track_titles]
        )
        logging.info(artist + " " + title)
        logging.info(track_titles)
        logging.info(closest_titles)
        if not closest_titles:
            return None
        i = [x[1] for x in track_titles].index(closest_titles[0])
        closest_track = [
            x for x in api_response \
                if x.id == track_titles[i][0]
        ][0]

        author = ""
        try:
            author = closest_track.author
        except AttributeError:
            author = closest_track.user["username"]
        soundcloud_track = SoundCloudTrack(
            id = str(closest_track.id),
            author = author,
            title = closest_track.title,
            duration = int(closest_track.duration)/1000
        )
        track = Track(
            id = "soundcloud_"+soundcloud_track.id,
            #artist = None,
            title = \
                soundcloud_track.author + " - " + soundcloud_track.title,
            duration_secs = soundcloud_track.duration,
            track_host = TrackHost.get_by_id(self.id).key
        )
        return track
