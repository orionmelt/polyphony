"""
urls.py

URL dispatch route mappings and error handlers

"""
from flask import render_template

from application import app
from application import views


## URL dispatch rules
# App Engine warm up handler
# See http://code.google.com/appengine/docs/python/config/appconfig.html#Warming_Requests
app.add_url_rule('/_ah/warmup', 'warmup', view_func=views.warmup)

# Route for homepage
app.add_url_rule('/', 'home', view_func=views.home)

# Route for playlist endpoint - returns playlist JSON
app.add_url_rule('/playlist', view_func=views.get_playlist_json)


# Route for kicking off crawls
app.add_url_rule('/crawl', view_func=views.crawl)
app.add_url_rule('/crawl/<frequency>', view_func=views.crawl)

# Route for one-time datastore initialization
app.add_url_rule('/init', view_func=views.initialize_datastore)

## Error handlers
# Handle 404 errors
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# Handle 500 errors
@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500
