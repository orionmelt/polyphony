import sys, os, re, urlparse, urllib2, logging
from datetime import datetime
import soundcloud, requests
from models import DataSource, TrackHost, Track, TrackMention
from google.appengine.ext import ndb
from collections import namedtuple

YOUTUBE_DATA_API_KEY = "AIzaSyAJ0em8O_2LVGBQhZAiDZnFZIPtDQw1j8Q"
SOUNDCLOUD_CLIENT_ID = "d3012111d6ea13fa210b214f82b7be3a"
HEADERS_FOR_REDDIT = {
	'User-Agent': 'Hot Sauce v0.1 by /u/orionmelt'
}

soundcloud_client = soundcloud.Client(client_id=SOUNDCLOUD_CLIENT_ID)

# We need this because results from SoundCloud could either be a Resource object or a dictionary.
SoundCloudTrack = namedtuple("SoundCloudTrack", "id author title duration")

def get_youtube_video_id(url):
	"""
	Given a YouTube video URL, parses the URL and returns YouTube video ID.

	"""
	video_id = None
	try:
		parsed_url = urlparse.urlparse(urllib2.unquote(url))
		if "youtube.com" in parsed_url.netloc:
			query_string = urlparse.parse_qs(parsed_url.query)
			query_string_dict = dict((k.lower(), v) for k, v in query_string.iteritems())
			if "v" in query_string_dict:
				video_id = query_string_dict["v"][0]
		elif "youtu.be" in parsed_url.netloc:
			video_id = parsed_url.path[1:]
	except:
		logging.exception("Unable to parse YouTube video ID from URL: %s" % url)
		pass
	
	return video_id

def get_youtube_track(url,video_id=None):
	"""
	Given a YouTube video url, constructs and returns a Track object.

	"""
	title = ""
	duration = 0
	track = None
	video_id = video_id or get_youtube_video_id(url)
	
	if not video_id:
		return None

	youtube_response = requests.get("https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails&key=%s&id=%s" % (YOUTUBE_DATA_API_KEY,video_id))
	youtube_response_json = youtube_response.json()

	# TODO - Error handling for rate-limiting, service unavailable, etc.

	if youtube_response_json["items"]:
		title = youtube_response_json["items"][0]["snippet"]["title"]
		duration = youtube_response_json["items"][0]["contentDetails"]["duration"]
		iso8601_minutes, iso8601_seconds = re.match("PT(\d+M)*(\d+S)*", duration).groups()
		minutes = int(iso8601_minutes[:-1]) if iso8601_minutes else 0
		seconds = int(iso8601_seconds[:-1]) if iso8601_seconds else 0

		logging.info(TrackHost.get_by_id("youtube").key)

		track = Track(
			id = "youtube_"+video_id,
			#artist = [None], # TODO - Try to get artist name using The Echo Nest API
			title = title,
			duration_secs = 60*minutes+seconds,
			track_host = TrackHost.get_by_id("youtube").key
		)

	return track

def search_youtube(artist, title):
	"""
	Given an artist and title, searches YouTube and returns first result as a Track object.

	"""
	track = None
	youtube_response = \
		requests.get("https://www.googleapis.com/youtube/v3/search?part=snippet&key=%s&q=%s" % (YOUTUBE_DATA_API_KEY,(artist+"+"+title).replace(" ","+")))
	youtube_response_json = youtube_response.json()
	if youtube_response_json["items"] and youtube_response_json["items"][0]["id"]["kind"] == "youtube#video":
		video_id = youtube_response_json["items"][0]["id"]["videoId"]
		track = Track.get_by_id("youtube_"+video_id)
		if not track:
			track = get_youtube_track("http://www.youtube.com/watch?v=%s" % video_id, video_id=video_id)
	return track

def get_soundcloud_track(url):
	"""
	Given a SoundCloud url, constructs and returns a Track object.

	"""
	track = None
	soundcloud_response = soundcloud_client.get('/resolve', url=url)
	soundcloud_track = None
	if soundcloud_response.kind == "track":
		author = ""
		try:
			author = soundcloud_response.author
		except AttributeError:
			author = soundcloud_response.user["username"]
		soundcloud_track = SoundCloudTrack(
			id = str(soundcloud_response.id), 
			author = author, 
			title = soundcloud_response.title, 
			duration = int(soundcloud_response.duration)/1000
		)
	elif soundcloud_response.kind == "playlist":
		author = ""
		try:
			author = soundcloud_response.tracks[0]["author"]
		except KeyError:
			author = soundcloud_response.tracks[0]["user"]["username"]
		soundcloud_track = SoundCloudTrack(
			id = str(soundcloud_response.tracks[0]["id"]),
			author = author, 
			title = soundcloud_response.tracks[0]["title"],
			duration = int(soundcloud_response.tracks[0]["duration"])/1000
		)

	if soundcloud_track:
		track = Track(
			id = "soundcloud_"+soundcloud_track.id,
			#artist = None,
			title = soundcloud_track.author + " - " + soundcloud_track.title,
			duration_secs = soundcloud_track.duration,
			track_host = TrackHost.get_by_id("soundcloud").key
		)

	return track

def search_soundcloud(artist, title):
	"""
	Given an artist and title, searches SoundCloud and returns closest result as a Track object.

	"""
	track = None
	soundcloud_response = soundcloud_client.get('/tracks', q=artist+" "+title, limit=10)
	search_tracks = [x for x in soundcloud_response if x.kind == "track" and title.lower() in x.title.lower()]
	if search_tracks:
		author = ""
		try:
			author = search_tracks[0].author
		except AttributeError:
			author = search_tracks[0].user["username"]
		soundcloud_track = SoundCloudTrack(
			id = str(search_tracks[0].id),
			author = artist,
			title = title,
			duration = int(search_tracks[0].duration)/1000
		)
		track = Track(
			id = "soundcloud_"+soundcloud_track.id,
			#artist = None,
			title = soundcloud_track.author + " - " + soundcloud_track.title,
			duration_secs = soundcloud_track.duration,
			track_host = TrackHost.get_by_id("soundcloud").key
		)
	return track

def crawl(refresh_frequency=60):
	"""
	Kicks off the data source crawl process.

	"""
	# Get list of data sources and crawl each source
	##data_sources = DataSource.query(DataSource.refresh_frequency==refresh_frequency).fetch()
	data_sources = DataSource.query().fetch()
	for data_source in data_sources:
		if data_source.source_type == "reddit":
			crawl_reddit(data_source)
			pass
		elif data_source.source_type == "hypem":
			crawl_hypem(data_source)
		else:
			# More sources later!
			pass

def crawl_reddit(data_source):
	"""
	Gets tracks data from subreddits.

	"""
	ds_name = "reddit"
	position = 0
	mentions = []
	tracks = []

	reddit_response = requests.get(data_source.source_url,headers=HEADERS_FOR_REDDIT)
	reddit_response_json = reddit_response.json()

	# TODO - Error handling for rate-limiting, service unavailable, etc.

	for submission in reddit_response_json["data"]["children"]:
		reddit_id = submission["data"]["id"].encode("ascii","ignore")
		subreddit = submission["data"]["subreddit"].encode("ascii","ignore")
		permalink = "http://www.reddit.com"+submission["data"]["permalink"].encode("ascii","ignore").lower()
		url = submission["data"]["url"].encode("ascii","ignore")
		reddit_title = submission["data"]["title"].encode("ascii","ignore")
		domain = submission["data"]["domain"].lower()

		# Now that we have the domain, let's see if it is a supported TrackHost.
		track_host = TrackHost.query(TrackHost.domains==domain).get()

		# TODO - Handle subdomains such as m.youtube.com
		
		logging.info(track_host)

		if not track_host:
			continue

		# Let's see if we've already processed this mention.
		mention = TrackMention.get_by_id(ds_name+"_"+reddit_id)
		if mention:
			# Yes we have, just update hotness score
			mention.hotness_score = position
			mentions.append(mention)
		else:
			if track_host.key.id()=="youtube":
				track = Track.get_by_id("youtube_"+str(get_youtube_video_id(url)))
				if not track:
					track = get_youtube_track(url)
					if not track:
						logging.info("No track: " + url)
						continue
					else:
						track.title = track.title or reddit_title
						tracks.append(track)
			elif track_host.key.id()=="soundcloud":
				track = get_soundcloud_track(url)
				if not track:
					logging.info("No track: " + url)
					continue
				if not Track.get_by_id(track.key.id()):
					track.title = track.title or reddit_title
					tracks.append(track)
			
			mention = TrackMention(
				id = ds_name+"_"+reddit_id,
				data_source = data_source.key,
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

def crawl_hypem(data_source):
	"""
	Gets tracks data from Hype Machine.

	"""
	ds_name = "hypem"

	mentions = []
	tracks = []

	hypem_response = requests.get(data_source.source_url)
	hypem_response_json = hypem_response.json()

	for key in hypem_response_json:
		logging.info(hypem_response_json[key])
		if not key.isdigit():
			continue
		artist = hypem_response_json[key]["artist"]
		title = hypem_response_json[key]["title"]
		hypem_post_id = str(hypem_response_json[key]["mediaid"])

		mention = TrackMention.get_by_id(ds_name+"_"+hypem_post_id)
		if not mention:
			# Search for this track on SoundCloud
			track = search_soundcloud(artist, title)
			# If no results, search on YouTube
			if not track:
				track = search_youtube(artist, title)
			# Well, let's give up
			if not track:
				continue
			if not Track.get_by_id(track.key.id()):
				tracks.append(track)
			mention = TrackMention(
				id = ds_name+"_"+hypem_post_id,
				data_source = data_source.key,
				track = track.key,
				mention_title = hypem_response_json[key]["sitename"],
				mention_url = hypem_response_json[key]["posturl"],
				hotness_score = int(key)
			)
			mentions.append(mention)
	if tracks:
		ndb.put_multi(tracks)
	if mentions:
		ndb.put_multi(mentions)

def initialize_datastore():
	r_music = DataSource(
		id = "r_music",
		source_type = "reddit",
		display_name = "reddit - /r/Music",
		source_url = "http://www.reddit.com/r/Music.json?limit=25",
		info_link = "http://www.reddit.com/r/Music",
		refresh_frequency = 60
	)

	r_music.put()

	r_listentothis = DataSource(
		id = "r_listentothis",
		source_type = "reddit",
		display_name = "reddit - /r/ListenToThis",
		source_url = "http://www.reddit.com/r/ListenToThis.json?limit=25",
		info_link = "http://www.reddit.com/r/ListenToThis",
		refresh_frequency = 60
	)

	r_listentothis.put()

	hypem = DataSource(
		id = "hypem",
		source_type = "hypem",
		display_name = "Hype Machine",
		source_url = "http://hypem.com/playlist/popular/noremix/json/1/data.js",
		info_link = "http://hypem.com",
		refresh_frequency = 240
	)

	hypem.put()

	youtube = TrackHost(
		id = "youtube",
		display_name = "YouTube",
		domains = ["youtu.be","youtube.com"]
	)

	youtube.put()

	soundcloud = TrackHost(
		id = "soundcloud",
		display_name = "SoundCloud",
		domains = ["soundcloud.com"]
	)

	soundcloud.put()