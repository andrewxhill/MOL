#!/usr/bin/env python
#
# Copyright 2010 Map Of Life
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from mapreduce import control as mr_control
from mol.db import TileUpdate

class InterpolateTiles(webapp.RequestHandler):
    def get(self):
        self.post()
    def post(self):
        t = TileUpdate.all().fetch(1)
        if len(t) == 1:
            mr_control.start_map(
              "Process queued Tiles stored in TileUpdate",
              "mappers.interpolate",
              "mapreduce.input_readers.DatastoreInputReader",
              {"entity_kind": "Tiles.TileUpdate",
              "shard_count": 2,
              },
              mapreduce_parameters={"done_callback": "/"},
            )
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.out.write('MR Cron Started')

application = webapp.WSGIApplication(
         [
          ('/cron/interpolate', InterpolateTiles)
         ],
         debug=True)


def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
