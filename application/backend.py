from google.appengine.ext import ndb
from models import DataSource, TrackHost
from track_hosts import SoundCloud, YouTube
from data_sources import Reddit, HypeMachine, NPR, Pitchfork


def crawl(refresh_frequency=60):
    """
    Kicks off the data source crawl process.

    """
    # Get list of data sources and crawl each source
    data_sources = DataSource.query(ndb.AND(DataSource.enabled == True, DataSource.refresh_frequency==refresh_frequency)).fetch()
    for data_source in data_sources:
        if data_source.source_type == "reddit":
            reddit = Reddit(data_source)
            reddit.crawl()
        elif data_source.source_type == "hypem":
            hypem = HypeMachine(data_source)
            hypem.crawl()
        elif data_source.source_type == "npr":
            npr = NPR(data_source)
            npr.crawl()
        elif data_source.source_type == "pitchfork":
            pitchfork = Pitchfork(data_source)
            pitchfork.crawl()
        else:
            # More sources later!
            pass



def initialize_datastore():
    r_music = DataSource(
        id = "r_music",
        source_type = "reddit",
        display_name = "Music on reddit",
        source_url = "http://www.reddit.com/r/Music.json?limit=25",
        info_link = "http://www.reddit.com/r/Music",
        refresh_frequency = 60,
        description = """/r/Music is the most popular subreddit about music, with over 6.5 million members."""


    )

    r_music.put()

    r_listentothis = DataSource(
        id = "r_listentothis",
        source_type = "reddit",
        display_name = "ListenToThis on reddit",
        source_url = "http://www.reddit.com/r/ListenToThis.json?limit=25",
        info_link = "http://www.reddit.com/r/ListenToThis",
        refresh_frequency = 60,
        description = """/r/ListenToThis is a place to discover music by new or overlooked artists, with over 2.5 million members."""
    )

    r_listentothis.put()

    hypem = DataSource(
        id = "hypem",
        source_type = "hypem",
        display_name = "Hype Machine",
        source_url = "http://hypem.com/playlist/popular/noremix/json/1/data.js",
        info_link = "http://hypem.com",
        refresh_frequency = 240,
        description = """Hype Machine keeps track of what music bloggers write about, with a carefully handpicked set of 855 music blogs."""
    )

    hypem.put()

    npr_allsongs = DataSource(
        id = "npr_allsongs",
        source_type = "npr",
        display_name = "NPR - All Songs Considered",
        source_url = "http://www.npr.org/rss/rss.php?id=15709577",
        info_link = "http://www.npr.org/blogs/allsongs/",
        refresh_frequency = 1440,
        enabled = False
    )

    npr_allsongs.put()

    pitchfork = DataSource(
        id = "pitchfork",
        source_type = "pitchfork",
        display_name = "Pitchfork",
        source_url = "http://pitchfork.com/rss/reviews/best/tracks/",
        info_link = "http://pitchfork.com/reviews/best/tracks/",
        refresh_frequency = 1440,
        description = """Pitchfork is a Chicago-based daily Internet publication devoted to music criticism and commentary, music news, and artist interviews."""
    )

    pitchfork.put()


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