# Copyright 2011 Aaron Steele
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

__author__ = "Aaron Steele (eightysteele@gmail.com)"
__contributors__ = []

import cache
import harvest
import sources
import tile

import logging
import os
import simplejson

from google.appengine.api import backends
from google.appengine.api import memcache
from google.appengine.api import taskqueue
from google.appengine.api import urlfetch
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template

class SearchPoints(webapp.RequestHandler):
    def get(self):
        self.post()

    def post(self):
        # Check parameters
        name = self.request.get('name', None)
        if not name:
            self.error(400)
            return
        source_name = self.request.get('source', None)
        
        # Check cache
        key = self.cache_key(name, source_name)
        names = cache.get(key)
        if names:
            self.response.set_status(200)
            self.response.headers['Content-Type'] = "application/json"
            self.response.out.write(names)
            return
        
        source = sources.get(source_name)
        if not source:
            # TODO: Get names from all sources?
            self.error(404)
            return
        
        # Make service request for names
        names, status_code = self.get_names(source, name)        
        if status_code != 200:
            self.error(status_code)
            return
        
        # Update cache and send response
        cache.add(key, names)
        self.response.set_status(200)
        self.response.headers['Content-Type'] = "application/json"
        self.response.out.write(simplejson.dumps(names))
        
    @classmethod
    def cache_key(cls, name, source_name):
        if source_name:
            return 'points-names-%s-%s' % (name, source_name)
        else:
            return 'points-names-%s' % name        

    @classmethod
    def get_names(cls, source, name):
        result = urlfetch.fetch(source.name_url(name))
        if result.status_code == 200:
            return (source.name_list(result.content), 200)
        else:
            return ([], result.status_code)

class HarvestPoints(webapp.RequestHandler):
    def get(self):
        self.error(405)
        self.response.headers['Allow'] = 'POST'
        return

    def post(self):
        # Check parameters
        name = self.request.get('name', None)
        source_name = self.request.get('source', None)
        if not name or not source_name:
            logging.info('Unable to harvest without name and source')
            self.error(400)
            return

        # Check cache for harvest job (handles polling)
        key = harvest.get_job_cache_key(name, source_name)
        job = cache.get(key)
        if job:
            self.response.set_status(200)
            self.response.headers['Content-Type'] = "application/json"
            self.response.out.write(simplejson.dumps(job))
            return
        else:
            cache.add(key, harvest.get_job(name, source_name, 'new'))
        
        # Add harvest task that targets harvest backed instance 1
        params = dict(name=name, source=source_name)
        taskqueue.add(url='/backend/harvest', target='harvest', params=params)
        self.response.set_status(202) # Accepted

class Home(webapp.RequestHandler):
    def get(self):
        template_values = dict(token='hi', limit=10, offset=0)
        self.response.out.write(template.render('index.html', template_values))

class TilePoints(webapp.RequestHandler):
    def get(self):
        tx = self.request.get_range('x', None)
        ty = self.request.get_range('y', None)
        z = self.request.get_range('z', None)
        limit = self.request.get_range('limit', min_value=1, max_value=1000, default=1000)
        offset = self.request.get_range('offset', min_value=0, default=0)
        name = self.request.get('name', None)
        source_name = self.request.get('source', None)
        if tx is None or ty is None or z is None or name is None or source_name is None:
            self.error(400)
            return
        tile_png = tile.get_tile_png(tx, ty, z, name, source_name, limit, offset, failfast=True)
        self.response.headers['Content-Type'] = 'image/png'
        self.response.out.write(tile_png)

        # Backend task for pre-rendering tiles at next 2 zoom levels
        # TODO: Figure out performance/cost tradeoff here
        params = dict(name=name, source=source_name, minzoom=z+1, maxzoom=z+1)
        taskqueue.add(url='/backend/render', target='render', params=params)
        
application = webapp.WSGIApplication([
        ('/frontend/points$', Home),
        ('/frontend/points/search', SearchPoints),
        ('/frontend/points/harvest', HarvestPoints),
        ('/frontend/points/tile', TilePoints),
        ], debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
