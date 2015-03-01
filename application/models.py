"""
models.py

Datastore models

"""

from google.appengine.ext import ndb

class DataSource(ndb.Model):
	"""
	Models a data source from which we can retrieve tracks data. For example, subreddits, blogs, etc.

	Attributes:
		id					- Unique ID string.
		source_type 		- Identifier for type of data source.
		display_name 		- Friendly name of the data source.
		source_url			- URL from which we can retrieve data (RSS feeds, API endpoints, etc.)
		info_link			- Public URL of the data source main page.
		refresh_frequency	- Refresh frequency value (in minutes) - tells us how often we should refresh data from this source. 
		date_added			- DateTime this data source entry was added.
		date_updated		- DateTime this data source entry was last updated.

	"""

	source_type = ndb.StringProperty()
	display_name = ndb.StringProperty(default="Unkown")
	source_url = ndb.TextProperty()
	info_link = ndb.TextProperty()
	refresh_frequency = ndb.IntegerProperty(default=60) 
	date_added = ndb.DateTimeProperty(auto_now_add=True)
	date_updated = ndb.DateTimeProperty(auto_now=True)


class TrackHost(ndb.Model):
	"""
	Models a website/service that hosts tracks. For example, YouTube, SoundCloud, etc.

	Attributes:
		id				- Unique ID string.
		display_name	- Friendly name of the track host.
		domains			- Top-level domains of the track host.
		date_added		- DateTime this track host entry was added.
		date_updated	- DateTime this track host entry was last updated.

	"""

	display_name = ndb.StringProperty(default="Unknown")
	domains = ndb.StringProperty(repeated=True)
	date_added = ndb.DateTimeProperty(auto_now_add=True)
	date_updated = ndb.DateTimeProperty(auto_now=True)


class Artist(ndb.Model):
	"""
	Models an individual artist/band.

	Attributes:
		id					- Unique ID string.
		display_name		- Friendly name of the artist.
		external_link		- Link to artist's website or biography elsewhere.
		image_url			- URL to artist photo.
		description			- Short description/intro about the artist.

	"""

	display_name = ndb.StringProperty()
	external_link = ndb.TextProperty(repeated=True)
	image_url = ndb.TextProperty(default="/static/img/artist_default.jpg")
	description = ndb.TextProperty()


class Track(ndb.Model):
	"""
	Models an individual track.

	Attributes:
		id				- Unique ID string (combination of TrackHost name and track ID we get from the TrackHost)
		title			- Track title
		artist			- One or more artists who performed this track.
		duration_secs	- Duration of this track in seconds.
		hosted_at		- Reference to TrackHost where the track is hosted.
	"""

	title = ndb.StringProperty()
	# TODO - Artist data
	#artist = ndb.KeyProperty(kind='Artist',repeated=True,default=None)
	duration_secs = ndb.IntegerProperty()
	track_host = ndb.KeyProperty(kind='TrackHost')


class TrackMention(ndb.Model):
	"""
	Models a mention entry - a reference to a track from a DataSource.

	Attributes:
		id				- Unique ID string (combination of DataSource name and DataSource's own post ID)
		data_source		- Reference to DataSource where this mention originated.
		track			- Reference to Track entity.
		mention_url		- URL where this track was mentioned.
		date_added		- Date this mention was first added.
		date_updated	- Date this mention was last updated.
		hotness_score	- A calculated hotness score to determine order in playlist.
	"""

	data_source = ndb.KeyProperty(kind='DataSource')
	track = ndb.KeyProperty(kind='Track')
	mention_title = ndb.StringProperty()
	mention_url = ndb.TextProperty()
	date_added = ndb.DateTimeProperty(auto_now_add=True)
	date_updated = ndb.DateTimeProperty(auto_now=True)
	hotness_score = ndb.IntegerProperty()
