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
from google.appengine.api import memcache as m, mail
import simplejson
import logging
from mol.db import MultiPolygon, MultiPolygonIndex
from google.appengine.ext import db

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
        
        
class Andrew(BaseHandler):
    """Handler for the search UI."""
    def get(self):
        """
        er = EcoregionLayer(
                name = 'candyland',
                id = 'NT0456',
                ecoCodes = ['NT0456', 'NT0457'],
                searchStrings = ['puma', 'concolor']
            )
        db.put(er)
        er = Ecoregion(
                key_name = "%s" % 'NT0405',
                ecoName = 'name',
                realm = 'realm',
                biome = 1,
                ecoNum = 3,
                ecoId = 4,
                g200Region = 'region',
                g200Num = 5,
                g200Biome = 8,
                g200Stat = 0
            )
        db.put(er)
        
        query = EcoregionSet.all()
        dsputs = []
        ct = 0
        for r in query.fetch(500):
                ss = {}
                er = []
                skipped = True
                for ek in r.ecoregions:
                    nm = ek.name()
                    nma = str(nm).split('/')
                    if len(nma) == 2:
                        er.append(db.Key.from_path('Ecoregion', nm))
                    else:
                        skipped = False
                        if len(nma)==1:
                            er.append(db.Key.from_path('Ecoregion', "wwf/%s" % nm))
                        else:
                            er.append(db.Key.from_path('Ecoregion', "wwf/%s" % nma[-1]))
                if skipped is False:
                    ct+=1
                    r.ecoregions = er
            dsputs.append(r.key())
        db.delete(dsputs)
        self.response.out.write("%s ER moves<br/>" % ct)
        """
        
        q = MultiPolygonIndex.all().filter('term','island').order('-rank')
        res = q.fetch(50)
        self.response.out.write("Search: 'island'<br/>")
        for r in res:
            self.response.out.write("<p>%s: %s<br/>" % (r.term,r.rank))
            self.response.out.write("dataset: %s</p>" % (r.parent().name))
            
        self.response.out.write("Andrew says %s" % 'hi')
            
        
      
application = webapp.WSGIApplication(
         [('/', MainPage),
          ('/latest', LatestHandler),
          ('/andrew', Andrew),
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
          ('/playground/col', ColPage),
          ('/sandbox/map', MapPage),
          ('/admin/flush-memcache', AdminFlushMemcacheHandler),
          ('/hooks/post-commit', GitHubPostReceiveHooksHandler), ],
         debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
