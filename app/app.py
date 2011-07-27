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
import random
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
import os
from google.appengine.api import memcache as m, mail
import simplejson
import logging
from mol.db import MetaData, MultiPolygonIndex, OccurrenceIndex, MasterSearchIndex, MultiPolygon
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
        self.render_template('map-index-template.html', {'prod': PROD, 'r': random.random()})
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
    SEND_LIST = ['eightysteele@gmail.com', 'tuco@berkeley.edu']

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
    """ Loads metadata from scripts in /utilities/metadata.
        Example:
        ./iucnranges.py -d /Users/tuco/Data/MoL/mol-data/range/shp/animalia/species/ -u http://tuco.mol-lab.appspot.com/metadataloader -k Metadata
    """
    def post(self):
        payload = self.request.get('payload')
        key_name = self.request.get('key_name')
        parent_key_name = self.request.get('parent_key_name')
        parent_kind = self.request.get('parent_kind')
        if not parent_key_name or not parent_kind:
            MetaData(
                key=db.Key.from_path('MetaData', key_name),
                object=payload).put()
        else:
            MetaData(
                key=db.Key.from_path(
                    parent_kind,
                    parent_key_name,
                    'MetaData',
                    key_name),
                object=payload).put()

class MultiPolygonLoader(BaseHandler):
    """ Loads MultiPolygons from scripts in /utilities/metadata.
        Example:
        ./iucnranges.py -d /Users/tuco/Data/MoL/mol-data/range/shp/animalia/species/ -u http://tuco.mol-lab.appspot.com/multipolygonloader -k MultiPolygon
    """
    def post(self):
        payload = self.request.get('payload')
        name=self.request.get('name')
        subname=self.request.get('subname')
        source=self.request.get('source')
        info=self.request.get('info')
        category=self.request.get('category')
        key_name = self.request.get('key_name')
        parent_key_name = self.request.get('parent_key_name')
        parent_kind = self.request.get('parent_kind')
        if not parent_key_name or not parent_kind:
            MultiPolygon(
                key=db.Key.from_path('MultiPolygon', key_name),
                object=payload,
                name=name,
                subname=subname,
                source=source,
                info=info,
                category=category
                ).put()
        else:
            MultiPolygon(
                key=db.Key.from_path(
                    parent_kind,
                    parent_key_name,
                    'MultiPolygon',
                    key_name),
                object=payload,
                name=name,
                subname=subname,
                source=source,
                info=info,
                category=category
                ).put()
    
class MultiPolygonIndexLoader(BaseHandler):
    """ Loads MultiPolygonIndexes from scripts in /utilities/metadata.
        Example:
        ./iucnranges.py -d /Users/tuco/Data/MoL/mol-data/range/shp/animalia/species/ -u http://tuco.mol-lab.appspot.com/multipolygonindexloader -k MultiPolygonIndex
    """
    def post(self):
        payload = self.request.get('payload')
        term=self.request.get('term')
        rank=int(self.request.get('rank'))
        key_name = self.request.get('key_name')
        parent_key_name = self.request.get('parent_key_name')
        parent_kind = self.request.get('parent_kind')
        if not parent_key_name or not parent_kind:
            MultiPolygonIndex(
                key=db.Key.from_path('MultiPolygonIndex', key_name),
                object=payload,
                term=term,
                rank=rank
                ).put()
        else:
            MultiPolygonIndex(
                key=db.Key.from_path(
                    parent_kind,
                    parent_key_name,
                    'MultiPolygonIndex',
                    key_name),
                object=payload,
                term=term,
                rank=rank
                ).put()
    
class MasterSearchIndexLoader(BaseHandler):
    """ Loads MasterSearchIndexes from scripts in /utilities/metadata.
        Example:
        ./iucnranges.py -d /Users/tuco/Data/MoL/mol-data/range/shp/animalia/species/ -u http://tuco.mol-lab.appspot.com/mastersearchindexloader -k MasterSearchIndex
    """
    def post(self):
        payload = self.request.get('payload')
        key_name = self.request.get('key_name')
        term=self.request.get('term')
        rank=int(self.request.get('rank'))
        parent_key_name = self.request.get('parent_key_name')
        parent_kind = self.request.get('parent_kind')
        if not parent_key_name or not parent_kind:
            MasterSearchIndex(
                key=db.Key.from_path('MasterSearchIndex', key_name),
                object=payload,
                term=term,
                rank=rank
                ).put()
        else:
            MasterSearchIndex(
                key=db.Key.from_path(
                    parent_kind,
                    parent_key_name,
                    'MasterSearchIndex',
                    key_name),
                object=payload,
                term=term,
                rank=rank
                ).put()
    
class TestDataLoader(BaseHandler):
    """Loads test data for use in a local instance of the datastore."""
    def get(self):
        # parent entity for puma concolor IUCN Range Map
        newkey = MultiPolygon(
                              key=db.Key.from_path('MultiPolygon','range/mol/animalia/species/puma_concolor'),
                              category="range",
                              info='{"extentNorthWest": "59.666250466,-135.365310669", "proj": "EPSG:900913", "extentSouthEast": "-53.106193543,-34.790122986"}', 
                              name="Puma concolor", 
                              source="IUCN", 
                              subname="IUCN Range Map").put()
        MultiPolygonIndex( term="puma concolor", 
                           parent = newkey, 
                           rank=1).put()
        # puma concolor MoL Range Map
        MasterSearchIndex( term="puma concolor", 
                           parent = newkey, 
                           rank=1).put()
        
        # parent entity for puma concolor WDPA Bioinventory Map
        newkey = MultiPolygon(key=db.Key.from_path('MultiPolygon', 'pa-group/wdpa-group/MA133'),
                           category="pa", 
                           info=None, 
                           name="Puma concolor", 
                           source="WDPA", 
                           subname="WDPA Bioinventory").put()
        # puma concolor WDPA Bioinventory Map
        MasterSearchIndex( term="puma concolor", 
                           parent = newkey, 
                           rank=2).put()
        # parent entity for puma concolor WWF Ecoregion Map
        newkey = MultiPolygon(key=db.Key.from_path('MultiPolygon', 'ecoregion-group/wwf/14766'),
                           category="ecoregion", 
                           info='{"description": "WildFinder database species-ecoregion dataset", "family": "Felidae", "species": "Puma concolor", "order": "Carnivora", "genus": "Puma", "class": "Mammalia"}', 
                           name="Puma concolor", 
                           source="WWF", 
                           subname="WWF Ecoregion Set").put()
        # puma concolor WWF Ecoregion Map
        MasterSearchIndex( term="puma concolor", 
                           parent = newkey, 
                           rank=3).put()
        # parent entity for rhea pennata Jetz Range Map
        newkey = MultiPolygon(key=db.Key.from_path('MultiPolygon','range/jetz/animalia/species/rhea_pennata'),
                           category="range", 
                           info='{"extentNorthWest": "59.666250466,-135.365310669", "proj": "EPSG:900913", "extentSouthEast": "-53.106193543,-34.790122986"}', 
                           name="Rhea pennata", 
                           source="Jetz", 
                           subname="Jetz Range Map").put()
        # rhea pennata Jetz Range Map
        MasterSearchIndex( term="rhea pennata", 
                           parent = newkey, 
                           rank=1).put()
        # rhea pennata Jetz Range Map
        MultiPolygonIndex( term="rhea pennata", 
                           parent = newkey, 
                           rank=1).put()
    
class TestDataInfo(BaseHandler):
    """Shows content of an Entity's info property."""
    def get(self):
        e = self.request.get('e')
        entities = e.split(',')
        for ent in entities:
            key = db.Key(encoded=ent)
            entity = db.get(key)
            self.response.out.write(entity.info)

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
          ('/layerwidget', LayerWidget),
          ('/map/.*', RangeMapHandler),
          ('/map', RangeMapHandler),
          ('/metadataloader', MetadataLoader),
          ('/multipolygonloader', MultiPolygonLoader),
          ('/multipolygonindexloader', MultiPolygonIndexLoader),
          ('/mastersearchindexloader', MasterSearchIndexLoader),
          ('/testdataloader', TestDataLoader),
          ('/testdatainfo', TestDataInfo),
          ('/playground/col', ColPage),
          ('/sandbox', MapPage),
          ('/sandbox/.*', MapPage),
          ('/admin/sandbox/.*', MapPage),
          ('/admin/flush-memcache', AdminFlushMemcacheHandler),
          ('/hooks/post-commit', GitHubPostReceiveHooksHandler), ],
         debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
