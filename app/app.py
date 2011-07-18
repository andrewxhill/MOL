#!/usr/bin/env python
#
# Copyright 2010 Andrew W. Hill, Aaron Steele
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
from google.appengine.api import memcache as m, mail
import simplejson
import logging
from mol.db import MetaData, MultiPolygonIndex, OccurrenceIndex ,MasterSearchIndex
from google.appengine.ext import db
import urllib
from google.appengine.api import apiproxy_stub, apiproxy_stub_map, urlfetch
from xml.etree import ElementTree as etree
import cStringIO, datetime, random
from google.appengine.api import images
import png

memcache = m.Client()

if 'SERVER_SOFTWARE' in os.environ:
  PROD = not os.environ['SERVER_SOFTWARE'].startswith('Development')
else:
  PROD = True

class ColPage(webapp.RequestHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), 'templates/coltest.html')
        self.response.out.write(template.render(path, {}))

class BaseHandler(webapp.RequestHandler):
    def render_template(self, f, template_args):
        path = os.path.join(os.path.dirname(__file__), "templates", f)
        self.response.out.write(template.render(path, template_args))

    def push_html(self, f):
        path = os.path.join(os.path.dirname(__file__), "html", f)
        self.response.out.write(open(path, 'r').read())

class PeoplePage(BaseHandler):
    def get(self):
        self.push_html('people.html')
        
class TechPage(BaseHandler):
    def get(self):
        self.push_html('tech.html')
        
class BlogPage(BaseHandler):
    def get(self):
        self.push_html('blog.html')
        
class DemoPage(BaseHandler):
    def get(self):
        self.push_html('demo.html')
        
class AboutPage(BaseHandler):
    def get(self):
        self.push_html('about.html')
        
class MainPage(BaseHandler):
    def get(self):
        self.push_html('home.html')

''' For testing... '''
class MapPage(BaseHandler):
    def get(self):
      self.render_template('map-index-template.html', {'prod': PROD})
        #self.push_html('map.html');
class LayerWidget(BaseHandler):
    def get(self):
        self.push_html('layer.widget.html')
''' For testing... '''

class AdminFlushMemcacheHandler(BaseHandler):
    def get(self):
        if not memcache.flush_all():
            self.response.out.write('Memcache failed to flush')
        else:
            self.response.out.write('Memcache flushed')
     
class GitHubPostReceiveHooksHandler(BaseHandler):    
    
    # Add your email address here if you want push notifications:
    SEND_LIST = ['eightysteele@gmail.com']
    
    def post(self):
        payload = self.request.get('payload')
        json = simplejson.loads(payload)
        title = '[%s] New GitHub activity - GIT push' % json['repository']['name']
        body = 'The following commits were just pushed:\n\n'
        for c in json['commits']:
            body += '%s\n' % c['message']
            body += '%s (author)\n' % c['author']['name']
            body += '%s\n' % c['timestamp']
            body += '%s\n\n' % c['url']
        logging.info(body)
        mail.send_mail(sender="Map of Life <admin@mol-lab.appspotmail.com>",
              to=', '.join(self.SEND_LIST),
              subject=title,
              body=body)     
            
class SearchHandler(BaseHandler):
    """Handler for the search UI."""
    def get(self):
        self.push_html("search.html")

class RangeMapHandler(BaseHandler):
    """Handler for the search UI."""
    def get(self):
        self.push_html("range_maps.html")

class LatestHandler(BaseHandler):
    """Handler for the search UI."""
    def get(self):
        self.redirect('http://biodiversity.colorado.edu/sandiego')
        
        
class William(BaseHandler):
    
    def xmltojson(self):
        coords = []
        n = 0
        while n<1000:
            x = random.randint(-1800,1800)
            y = random.randint(-900,900)
            c = random.randint(10,10000)
            coords.append({
                "coordinates": {
                    "decimalLongitude": float(x)/10,
                    "decimalLatitude": float(y)/10,
                    "coordinateUncertaintyInMeters": float(c)/10
                    }
                });
            n+=1
                    
        return coords
    def get(self):
        self.post()
    def post(self):
        query = {'layerName': 'Puma concolor'}
        self.gbifjson = self.xmltojson()
        self.response.headers['Content-Type'] = "application/json"
        self.response.out.write(simplejson.dumps(self.gbifjson)) 
        
class Andrew(BaseHandler):
    def get(self):
        self.post()
    def post(self):
        m.flush_all()
        self.response.out.write("<p>Andrew says %s</p>" % 'hi')

class MetadataLoader(BaseHandler):
    def post(self):
        payload = self.request.get('payload')
        key_name = self.request.get('key_name')
        parent_key_name = self.request.get('parent_key_name')
        parent_kind = self.request.get('parent_kind')
        key = db.Key.from_path(
          parent_kind, 
          parent_key_name,
          'MetaData',
          key_name)
        MetaData(key=key, object=payload).put()
    
    
application = webapp.WSGIApplication(
         [('/', MainPage),
          ('/latest', LatestHandler),
          ('/andrew', Andrew),
          ('/william', William),
          ('/about', AboutPage),
          ('/tech', TechPage),
          ('/demo', DemoPage),
          ('/blog', BlogPage),
          ('/people', PeoplePage),
          ('/search', SearchHandler),
          ('/latest', LatestHandler),
          ('/layerwidget', LayerWidget),
          ('/map/.*', RangeMapHandler),
          ('/map', RangeMapHandler),
          ('/metadataloader', MetadataLoader),
          ('/playground/col', ColPage),
          ('/sandbox', MapPage),
          ('/sandbox/.*', MapPage),
          ('/admin/flush-memcache', AdminFlushMemcacheHandler),
          ('/hooks/post-commit', GitHubPostReceiveHooksHandler), ],
         debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
