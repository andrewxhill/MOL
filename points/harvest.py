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
from google.appengine.api import taskqueue
from google.appengine.api import urlfetch
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from ndb import model

def get_job_cache_key(name, source_name):
    return 'points-harvest-job-%s-%s' % \
        (name.strip().lower(), source_name.strip().lower())

def get_job(name, source_name, status, msg=None):
    return dict(
        id=get_job_cache_key(name, source_name), 
        status=status,
        msg=msg)    

class Harvest(webapp.RequestHandler):
    def get(self):
        self.error(405)
        self.response.headers['Allow'] = 'POST'
        return

    def post(self):
        # Parameters checked by frontend
        name = self.request.get('name')
        source_name = self.request.get('source')

        # Get source
        source = sources.get(source_name)
        if not source:
            logging.error('Cannot harvest without a source')
            self.error(404)
            # Update job status to 'error'
            job = get_job(name, source_name, 'error', msg='Unsupported source')
            cache.add(key, job)
            return

        # Check cache for harvest job 
        key = get_job_cache_key(name, source_name)
        job = cache.get(key)
        if not job:
                self.error(404)
                self.response.headers['Content-Type'] = "application/json"
                self.response.out.write('{"error":"unknown job %s"}' % key)
                return
            
        count = 0

        # Update job status to 'working'
        cache.add(key, get_job(name, source_name, 'working', msg=count))       

        # Get points from source and put them into datastore in batches
        for points in self.get_points(name, source):
            model.put_multi(
                [PointIndex.create(p[0], p[1], name, source_name) \
                     for p in points])
            # Update job with count
            count += len(points)
            cache.add(key, get_job(name, source_name, 'working', msg=count))

        # Update job status to 'done'
        # TODO: Done now or after backend rendering completes?
        cache.add(key, get_job(name, source_name, 'done', msg=count))

        # TODO: Decide if this is a good tradeoff between cost/performance
        # Backend task for pre-rendering tiles for lower zooms
        params = dict(name=name, source=source_name, minzoom=0, maxzoom=3)
        taskqueue.add(url='/backend/render', target='render', params=params)
 
    @classmethod
    def get_points(cls, name, source):
        """Generator for source points."""
        content = None
        # TODO: How to do this in parallel with async urlfetch?
        while True:
            points, url = source.get_points(name, content=content)
            yield points
            if not url:
                break
            content = urlfetch.fetch(url, deadline=10).content

application = webapp.WSGIApplication([
     ('/backend/harvest', Harvest),
     ],
     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
