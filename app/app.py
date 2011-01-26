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
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
import os

class ColPage(webapp.RequestHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), 'templates/coltest.html')
        self.response.out.write(template.render(path, {}))

class MapPage(webapp.RequestHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), 'templates/maptest.html')
        self.response.out.write(template.render(path, {}))

class MainPage(webapp.RequestHandler):
    def get(self):
        self.response.out.write('hi')

class BaseHandler(webapp.RequestHandler):
    def render_template(self, file, template_args):
        path = os.path.join(os.path.dirname(__file__), "templates", file)
        self.response.out.write(template.render(path, template_args))

class ColSearchHandler(BaseHandler):
    """Handler for the COL search UI."""
    def get(self):
        self.render_template("pager.html", {})

application = webapp.WSGIApplication(
         [('/', MainPage),
          ('/col/search', ColSearchHandler),
          ('/playground/col', ColPage),
          ('/playground/map', MapPage)],
         debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
