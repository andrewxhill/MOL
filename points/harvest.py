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
import sources
from model import PointIndex

import logging
import simplejson

from google.appengine.api import backends
from google.appengine.api import urlfetch
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from ndb import model

class Harvest(webapp.RequestHandler):
    def get(self):
        self.error(405)
        self.response.headers['Allow'] = 'POST'
        return

    def post(self):
        # Check parameters
        name = self.request.get('name', None)
        if not name:
            self.error(400)
            return
        source_name = self.request.get('source', None)
        
        # Get source
        source = sources.get(source_name)
        if not source:
            # TODO: Get points from all sources?
            logging.error('Cannot harvest without a source')
            self.error(404)
            return

        # Get points and put them into datastore
        for points in self.get_points(name, source):
            model.put_multi(
                [PointIndex.create(p[0], p[1], name, source_name) \
                     for p in points])

        # TODO: Task for pre-rendering zooms 0-9
 
    @classmethod
    def get_points(cls, name, source):
        """Generator for source points."""
        content = None
        while True:
            points, url = source.get_points(name, content=content)
            yield points
            if not url:
                break
            content = urlfetch.fetch(url).content

application = webapp.WSGIApplication([
     ('/backend/harvest', Harvest),
     ],
     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
