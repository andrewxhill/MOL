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

import tile

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

def render_tile(zoom, name, source_name, limit, offset):
    for z in range(zoom):
        tile_dimension = 1 << z
        for tx in range(tile_dimension):
            for ty in range(tile_dimension):
                tile.get_tile_png(tx, ty, z, name, source_name, limit, offset)

class Render(webapp.RequestHandler):
    def get(self):
        self.error(405)
        self.response.headers['Allow'] = 'POST'
        return

    def post(self):
        limit = self.request.get_range('limit', min_value=1, max_value=1000, default=1000)
        offset = self.request.get_range('offset', min_value=0, default=0)
        name = self.request.get('name')
        source_name = self.request.get('source')
        minzoom = self.request.get_range('minzoom', min_value=0, max_value=15, default=0)
        maxzoom = self.request.get_range('maxzoom', min_value=0, max_value=15, default=1)
        
        # TODO: How to run this in parallel?
        for z in range(minzoom, maxzoom + 1): 
            render_tile(z, name, source_name, limit, offset)

application = webapp.WSGIApplication([
     ('/backend/render', Render),
     ],
     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
