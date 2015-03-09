"""
views.py

URL route handlers

"""
from decorators import admin_required
from flask import request, render_template, url_for, redirect, jsonify
from flask_cache import Cache
from application import app
from google.appengine.ext import ndb
from models import DataSource, Track, TrackMention
import backend, logging

# Flask-Cache (configured to use App Engine Memcache API)
cache = Cache(app)

def get_all_data_sources():
    all_data_sources = DataSource.query(DataSource.enabled == True).order(DataSource.source_type).fetch()
    return all_data_sources

def get_playlist(data_sources=None):
    if data_sources:
        data_source_keys = [ndb.Key("DataSource", x) for x in data_sources if x]
        logging.info(data_source_keys)
        mentions = TrackMention.query(TrackMention.data_source.IN(data_source_keys)).order(-TrackMention.date_updated).fetch(100)
    else:
        mentions = TrackMention.query().order(-TrackMention.date_updated).fetch(100)
    playlist = []

    for mention in mentions:
        track = mention.track.get()
        track_host = track.track_host.get()
        data_source = mention.data_source.get()
        playlist_item = {
            "id": track.key.id().split("_",1)[1],
            "title": track.title,
            "duration": "%02d:%02d" % divmod(track.duration_secs, 60),
            "track_host": track_host.key.id(),
            "data_source_id": data_source.key.id(),
            "data_source_name": data_source.display_name,
            "mention_title": mention.mention_title,
            "mention_url": mention.mention_url,
            "hotness_score": mention.hotness_score
        }
        playlist.append(playlist_item)

    return sorted(playlist, key=lambda x:x["hotness_score"])

def get_playlist_json():
    data_sources = request.args.get("data_sources").split(",") if request.args.get("data_sources") else None
    playlist = get_playlist(data_sources=data_sources)
    return jsonify(playlist=playlist)

#@cache.cached(timeout=1800)
def home():
    return render_template('index.html', playlist=get_playlist(), data_sources=get_all_data_sources())

def crawl(frequency=60):
    backend.crawl(int(frequency))
    return "OK"

@admin_required
def initialize_datastore():
    backend.initialize_datastore()
    return "OK"

def warmup():
    """App Engine warmup handler
    See http://code.google.com/appengine/docs/python/config/appconfig.html#Warming_Requests

    """
    return ''

