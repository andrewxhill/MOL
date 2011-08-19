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
import math
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
import re

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
    """ Loads metadata for a data collection from scripts in /utilities/metadata.

        Example:
        ./jetzranges.py -d ~/Data/MoL/mol-data/test/range/jetz -u http://localhost:8080/metadataloader -c loadmetadata -t Latin
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

class EntityLoader(BaseHandler):
    """ Loads MultiPolygons, MasterSearchIndexes, and Metadata from scripts in /utilities/metadata.
        Example:
        ./jetzranges.py -d ~/Data/MoL/mol-data/test/range/jetz -u http://localhost:8080/entityloader -c loadentities -t Latin
    """
    def post(self):
        mdpayload = self.request.get('mdpayload')
        name=self.request.get('name')
        subname=self.request.get('subname')
        source=self.request.get('source')
        info=self.request.get('info')
        category=self.request.get('category')
        key_name = self.request.get('key_name')
        parent_key_name = self.request.get('parent_key_name')
        term = self.request.get('term').lower()

        """Publish the MultiPolygon entity, the parent to remainder of the entities to load."""
        newkey = MultiPolygon(
            key=db.Key.from_path('MultiPolygon', key_name),
            name=name,
            subname=subname,
            source=source,
            info=info,
            category=category
            ).put()
        """Publish the MetaData entity for the layer."""
        MetaData(
                 key=db.Key.from_path(
                 'MultiPolygon',
                 parent_key_name,
                 'MetaData',
                 key_name),
                 object=mdpayload
                 ).put()
        """ Publish the MasterSearchIndex entity for the layer, including the full
            term and combinations of its tokens."""
        tokenlist = multitokenize(term,' ')
        tokencount = len(term.split(' '))
        for token in tokenlist:
            rank=int(100*len(token.split(' '))/tokencount)
            if token == term.split(' ')[0]:
                rank=50
            MasterSearchIndex( term=token, 
                               parent = newkey, 
                               rank=rank).put()

        # TODO: Are MultiPolygonIndexes still needed? They were the same as MasterSearchIndexes
#        MultiPolygonIndex( term=term,
#                           parent = newkey, 
#                           rank=90).put()

class TestDataLoader(BaseHandler):
    """Loads test data for use in a local instance of the datastore."""
    def get(self):
        term = "Struthio camelus"
        newkey = MultiPolygon(key=db.Key.from_path('MultiPolygon','range/jetz/animalia/species/struthio_camelus'),
                           category="range", 
                           info='{"extentNorthWest": "59.666250466,-135.365310669", "proj": "EPSG:900913", "extentSouthEast": "-53.106193543,-34.790122986"}', 
                           name=term, 
                           source="Jetz", 
                           subname="Jetz Test Range Map").put()
        tokenlist = multitokenize(term.lower(),' ')
        tokencount = len(term.split(' '))
        for token in tokenlist:
            rank=int(100*len(token.split(' '))/tokencount)
            if token == term.split(' ')[0]:
                rank=50
            MasterSearchIndex( term=token, 
                               parent = newkey, 
                               rank=rank).put()
    
#        # parent entity for puma concolor IUCN Range Map
#        newkey = MultiPolygon(
#                              key=db.Key.from_path('MultiPolygon','range/mol/animalia/species/puma_concolor'),
#                              category="range",
#                              info='{"extentNorthWest": "59.666250466,-135.365310669", "proj": "EPSG:900913", "extentSouthEast": "-53.106193543,-34.790122986"}', 
#                              name="Puma concolor", 
#                              source="IUCN", 
#                              subname="IUCN Range Map").put()
#        MultiPolygonIndex( term="puma concolor", 
#                           parent = newkey, 
#                           rank=1).put()
#        # puma concolor MoL Range Map
#        MasterSearchIndex( term="puma concolor", 
#                           parent = newkey, 
#                           rank=1).put()
#        
#        # parent entity for puma concolor WDPA Bioinventory Map
#        newkey = MultiPolygon(key=db.Key.from_path('MultiPolygon', 'pa-group/wdpa-group/MA133'),
#                           category="pa", 
#                           info=None, 
#                           name="Puma concolor", 
#                           source="WDPA", 
#                           subname="WDPA Bioinventory").put()
#        # puma concolor WDPA Bioinventory Map
#        MasterSearchIndex( term="puma concolor", 
#                           parent = newkey, 
#                           rank=2).put()
#        # parent entity for puma concolor WWF Ecoregion Map
#        newkey = MultiPolygon(key=db.Key.from_path('MultiPolygon', 'ecoregion-group/wwf/14766'),
#                           category="ecoregion", 
#                           info='{"description": "WildFinder database species-ecoregion dataset", "family": "Felidae", "species": "Puma concolor", "order": "Carnivora", "genus": "Puma", "class": "Mammalia"}', 
#                           name="Puma concolor", 
#                           source="WWF", 
#                           subname="WWF Ecoregion Set").put()
#        # puma concolor WWF Ecoregion Map
#        MasterSearchIndex( term="puma concolor", 
#                           parent = newkey, 
#                           rank=3).put()
    
class TestDataInfo(BaseHandler):
    """Shows content of an Entity's info property."""
    def get(self):
        e = self.request.get('e')
        entities = e.split(',')
        for ent in entities:
            key = db.Key(encoded=ent)
            entity = db.get(key)
            self.response.out.write(entity.info)

def multitokenize(term, separator=' '):
    """ 
        Return a list of all distinct combinations of tokens separated by separator in a term.
    
        Arguments:
            term - the string for which to find token combinations
            separator - an optional string of characters to use as the token separator (default is ' ')
    """
    termlist=[]
    # Regular expression to match any combination of the separator string, spaces, and tabs
    sep = '[%s \t]+' % separator
    # Use the regular expression to separate tokens into a list
    tokenlist = re.split(sep, term.lstrip().rstrip())
    listcount = len(tokenlist)
    # Determine the number of distinct, non-empty combinations of tokens
    combos = int(math.pow(2,len(tokenlist))-1)
    # Iterate through the integers represented by combos starting at 1
    for n in range(1,combos+1):
        newterm=''
        # Iterate through the indexes of every token in the list of tokens
        for i in range(listcount):
            # If the index has an "on" bit in the bitwise representation of combos, include it in the newterm
            # Example: term = 'puma concolor'
            #  tokenlist = ['puma','concolor']
            #  combos = 3
            #  n=1, i=0, (n>>i)%2 = 1, newterm=' puma'
            #  n=1, i=1, (n>>i)%2 = 0
            #    -> add 'puma' to termlist
            #  n=2, i=0, (n>>i)%2 = 0, newterm=''
            #  n=2, i=1, (n>>i)%2 = 1, newterm=' concolor'
            #    -> add 'concolor' to termlist
            #  n=3, i=0, (n>>i)%2 = 1, newterm=' puma'
            #  n=3, i=1, (n>>i)%2 = 1, newterm=' puma concolor'
            #    -> add 'puma concolor' to termlist
            if (n>>i)%2==1:
                newterm='%s %s' % (newterm, tokenlist[i])
        termlist.append(newterm.lstrip().rstrip())
    # make sure there are no duplicates in the returned list
    return list(set(termlist))


class Insane(BaseHandler):
    def get(self):
        # Contact.query(Contact.address == Address(city='San Francisco', street='Spear St'))
        from ndb import model
        from mol.db.layers import LayerIndex, LayerPolygon
        s = self.request.get('s')
        p = self.request.get('p')
        a = self.request.get('a')
        r = self.request.get('r')
        #qry = LayerIndex.query(LayerIndex.polygons.specieslatin == 'dry chaco',
        #                       LayerIndex.polygons.polygonid == '2')
        qry = LayerIndex.query(LayerIndex.polygons == LayerPolygon(
                specieslatin='815.02300000000',
                polygonid='14730',
                source='4936.88958455000',
                areaid='9111848.92186000012'))
        #qry = LayerIndex.query(LayerIndex.creator == 'Walter')
        json = simplejson.dumps([simplejson.loads(x.parent().get().json) for x in qry.fetch(keys_only=True)])
        self.response.headers["Content-Type"] = "application/json"
        self.response.out.write(json)
    
INDEXED_PROPS = ['accessright', 'accessright', 'accessrights', 'areaid', 
                 'bibliographiccitation', 'bibliographiccitation', 
                 'breedingdomain', 'contact', 'contributor', 'contributor', 
                 'coverage', 'date', 'email', 'eventdate', 'format', 'format', 
                 'identifier', 'identifier', 'nonbreedingdomain', 'polygonid', 
                 'polygonname', 'presencedefault', 'rights', 'rights', 
                 'samplingprotocol', 'scientificname', 'scientificname', 
                 'source', 'surveyintervals', 'surveyintervals', 'type', 'type', 
                 'verbatimsrs']
    
POLYGON_PROPS = ['areaid', 'areaname', 'bibliographiccitation', 'contributor', 
                 'dateend', 'datestart', 'establishmentmeans', 
                 'infraspecificepithet', 'occurrencestatus', 'polygonid', 
                 'polygonname', 'scientificname', 'seasonality']

class NewLayerApi(BaseHandler):

    """Prototype class for experimenting with new Layers API."""

    def get(self):
        
        from ndb import model, query
        from mol.db.layers import Layer, LayerIndex

        limit = self.request.get_range('limit', min_value=1, max_value=100, default=10)
        offset = self.request.get_range('offset', min_value=0, default=0)
        args = {}
        for arg in self.request.arguments():
            if arg in INDEXED_PROPS:
                if arg in POLYGON_PROPS:
                    args['polygon.%s' % arg] = self.request.get(arg, None)
                else:
                    args[arg] = self.request.get(arg, None)
            
        qry = LayerIndex.query()
        if len(args) > 0:
            gql = 'SELECT * FROM LayerIndex WHERE'
            for k,v in args.iteritems():
                gql = "%s \"%s\" = '%s' AND " % (gql, k, v)
            gql = gql[:-5] # Removes trailing AND
            logging.info(gql)
            qry = query.parse_gql(gql)[0]
        # No keyword search yet
        #for keyword in keywords:
        #    qry = qry.filter(RecordIndex.corpus == keyword)        
        logging.info('QUERY='+str(qry))
        layers = model.get_multi(set([x.parent() for x in qry.fetch(limit, offset=offset, keys_only=True)]))
        layers_json = [simplejson.loads(x.json) for x in layers]
        self.response.headers["Content-Type"] = "application/json"
        self.response.out.write(simplejson.dumps(layers_json))

class NewPolygonApi(BaseHandler):
    """This is a prototype class for experimenting with the new Polygon API."""

    def get(self):
        
        from ndb import model, query
        from mol.db.layers import Layer, LayerIndex

        limit = self.request.get_range('limit', min_value=1, max_value=100, default=10)
        offset = self.request.get_range('offset', min_value=0, default=0)
        args = {}
        for arg in self.request.arguments():
            if arg in POLYGON_PROPS:
                args['polygon.%s' % arg] = self.request.get(arg, None)
            
        qry = LayerIndex.query()
        if len(args) > 0:
            gql = 'SELECT * FROM LayerIndex WHERE'
            for k,v in args.iteritems():
                gql = "%s \"%s\" = '%s' AND " % (gql, k, v)
            gql = gql[:-5] # Removes trailing AND
            logging.info(gql)
            qry = query.parse_gql(gql)[0]
        logging.info('QUERY='+str(qry))
        polygons = []
        for x in qry.fetch(limit, offset=offset): #[simplejson.loads(x.json) for x in qry.fetch(limit, offset=offset)]
            p = simplejson.loads(x.json)
            p['layer_index_key'] = str(x.key.id())
            p['layer_key'] = str(x.key.parent().id())
            polygons.append(p)
        self.response.headers["Content-Type"] = "application/json"
        self.response.out.write(simplejson.dumps(polygons))

application = webapp.WSGIApplication(
         [('/', MainPage),
          ('/nla', NewLayerApi),
          ('/npa', NewPolygonApi),
          ('/insane', Insane),
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
          ('/entityloader', EntityLoader),
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
