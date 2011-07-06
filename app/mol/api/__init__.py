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
from django.utils import simplejson
from google.appengine.api import urlfetch, memcache
from google.appengine.api.datastore_errors import BadKeyError, BadArgumentError
from google.appengine.api.memcache import Client
from google.appengine.ext import webapp, db
from google.appengine.ext.db import KindError
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from gviz import gviz_api
from mol.db import Species, SpeciesIndex, Tile, MetaDataIndex, MetaData
from xml.etree import ElementTree as etree
import datetime
import logging
import re
import os
import pickle
import time
import wsgiref.util
import StringIO
from mol.service import MasterTermSearch
from mol.service import TileService
from mol.service import LayerService
from mol.service import MetadataProvider
from mol.service import OverviewImageProvider
from mol.service import GbifLayerProvider
from mol.service import LayerType
from mol.service import LayerService
from mol.service import png
from mol.service import colorPng

HTTP_STATUS_CODE_NOT_FOUND = 404
HTTP_STATUS_CODE_FORBIDDEN = 403
HTTP_STATUS_CODE_BAD_REQUEST = 400

class BaseHandler(webapp.RequestHandler):
    '''Base handler for handling common stuff like template rendering.'''

    def _param(self, name, required=True, type=str):
        # Hack (see http://code.google.com/p/googleappengine/issues/detail?id=719)
        import cgi
        params = cgi.parse_qs(self.request.body)
        if len(params) is 0:
            val = self.request.get(name, None)
        else:
            if params.has_key(name):
                val = params[name][0]
            else:
                val = None

        # val = self.request.get(name, None)
        if val is None:
            if required:
                logging.error('%s is required' % name)
                raise BadArgumentError
            return None
        try:
            return type(val)
        except (ValueError), e:
            logging.error('Invalid %s %s: %s' % (name, val, e))
            raise BadArgumentError(e)

    def render_template(self, file, template_args):
        path = os.path.join(os.path.dirname(__file__), "../../templates", file)
        self.response.out.write(template.render(path, template_args))

    def push_html(self, file):
        path = os.path.join(os.path.dirname(__file__), "../../html", file)
        self.response.out.write(open(path, 'r').read())
        
class WebAppHandler(BaseHandler):
    
    def __init__(self):
        self.layer_service = LayerService()
        self.gbif = GbifLayerProvider()
        self.metadata = MetadataProvider()
        
    def get(self):
        self.post();

    def post(self):
        action = self.request.get('action', None)
        
        if not action:
            self.error(400) # Bad request
            return

        action = simplejson.loads(action)
        a_name = action.get('name')
        a_type = action.get('type')
        a_query = action.get('params')
        logging.info('name=%s, type=%s, query=%s' % (a_name, a_type, a_query))
        
        response = {
            'LayerAction': {
                'search': lambda x: self._layer_search(x),
                'get-points': lambda x: self._layer_get_points(x),
                'metadata-item': lambda x: self._layer_get_metadata(x),
                }
            }[a_name][a_type](a_query)

        self.response.headers["Content-Type"] = "application/json"
        self.response.out.write(simplejson.dumps(response))
        
    def _layer_get_points(self, query):
        # TODO: Use self.layer_service()
        sciname = query.get('layerName')
        query['sciname'] = sciname
        content = self.gbif.getdata(query)
        return content
        
    def _layer_get_metadata(self, query):
        # TODO: Use self.layer_service()
        key_name = query.get('key_name')
        content = self.metadata.getitem({'key_name':key_name})
        return content
        
        
    def _layer_search(self, query):
        # TODO(aaron): Merge list of profiles.
        # return self.layer_service.search(query)[0]
        term = query.get('query', 'stenocercus')
        if term in ["", None, False]:
            term = 'stenocercus'
        limit = int(query.get('limit', 500))
        offset = int(query.get('offset', 0))
        
        query = {"term": term, "limit": limit, "offset": offset}
        mts = MasterTermSearch(query)
        return mts.api_format()

class OverviewImageHandler(BaseHandler):
    
    def get(self):
        #range/mol/animalia/species/abditomys_latidens
        key_name = self.request.params.get('key_name', 'ecoregion/wwf/100') #or ecoregion, or protected area
        #datatype = self.request.params.get('type', 'range').lower() #or ecoregion, or protected area
        h = int(self.request.params.get('h', 500))
        w = int(self.request.params.get('w', 500))
        
        params = {'key_name': key_name,
                  'height': h,
                  'width': w }
                  
        ov = OverviewImageProvider(params)
        ov.getimg()
        logging.error(ov.url)
        if ov.img is not None:
            self.response.headers['Content-Type'] = "image/png"
            self.response.out.write(ov.img)
        else:
            self.error(204)
            return self.response.set_status(204)
    
class PointsHandler(BaseHandler):
    '''RequestHandler for GBIF occurrence point datasets
       Uses the GbifLayerProvider Service to return GBIF datasets
       
       Required query string parameters:
          sciname - string scientific name for point dataset
          
       Optional query string parameters:
          limit - integer number of records to return
          start - integer offset for paging of records
          source - string source of dataset, default and only gbif right now
    '''
    def __init__(self):
        super(PointsHandler, self).__init__()
        self.gbif = GbifLayerProvider()
        #self.ts = TileService()
        
    def post(self):
        src = self.request.params.get('source', 'gbif')
        lim = self.request.params.get('limit', 200)
        sta = self.request.params.get('start', 0)
        sn = self.request.params.get('sciname', "Puma concolor")
        query = {"limit": lim,
                 "start": 0,
                 "coordinatestatus": True,
                 "format": "darwin",
                 "sciname": sn,
                }
        url = self.gbif.geturl(query)
        data = self.gbif.getdata(query)
        self.response.headers['Content-Type'] = "application/json"
        self.response.out.write(simplejson.dumps(data)) # Not found

    def get(self):
        self.post()
            
class TileHandler(BaseHandler):
    '''Handles a PNG map tile request according to the Google XYZ tile
       addressing scheme described here:

       http://code.google.com/apis/maps/documentation/javascript/v2/overlays.html#Google_Maps_Coordinates

       Required query string parameters:
    '''
    
    def get(self):
        #range/mol/animalia/species/abditomys_latidens
        key_name = self.request.params.get('key_name', 'ecoregion/wwf/100') #or ecoregion, or protected area
        #datatype = self.request.params.get('type', 'range').lower() #or ecoregion, or protected area
        x = int(self.request.params.get('x', 0))
        y = int(self.request.params.get('y', 0))
        z = int(self.request.params.get('z', 0))
        r = self.request.params.get('r', 0)
        g = self.request.params.get('g', 0)
        b = self.request.params.get('b', 0)
        queue = True if self.request.params.get('queue', None) is None else False
        tp = None
        
        d = key_name.split('/', 2)
        datatype, source, id = d[0],d[1],d[2]
        
        tp = TileService({
                'type': datatype.lower(),
                'source': source.lower(),
                'id': id,
                'z': z,
                'x': x,
                'y': y,
                'r': r,
                'g': g,
                'b': b,
                'queue': queue })
        tp.gettile()
        if tp.status == 200:
            if queue:
                self.response.headers['Content-Type'] = "image/png"
                self.response.out.write(tp.png)
                return
            else:
                return self.response.set_status(200)
        elif tp.status == 204:
            return self.response.set_status(200)
        elif tp.status == 300:
            url = tp.url + "&retry=1"
            self.redirect(url)
        else: 
            self.error(404)
            return self.response.set_status(404)
    
class TaxonomyHandler(BaseHandler):
    '''RequestHandler for Taxonomy query
    
       Required query string parameters:
          
       Optional query string parameters:
          key - if given will do a direct key only search for the result
          names
          authorityName
          authorityIdentifier
          kingdom
          phylum
          class
          order
          superFamily
          family
          genus
          species
          infraSpecies
          hasRangeMap - boolean, if True will only return mapped results, no false filter yet
          simple - if given will return a simple result object, not full Species entry
    '''
    def __init__(self):
        super(TaxonomyHandler, self).__init__()
        self.taxonomy = TaxonomySearch()
        #self.ts = TileService()
    
    def get(self):
        if self.request.params.get('key', None) is not None:
            if self.request.params.get('simple', None) is not None:
                data = self.taxonomy.getdata({'key': self.request.params.get('key')})
            else:
                data = self.taxonomy.getdata({'key': self.request.params.get('key')})
            
            
        else: 
            query = {}
            params = ['limit',
                      'offset']
                      
            for p in params:
                if self.request.params.get(p, None) is not None:
                    query[p] = self.request.params.get(p) 
            
            filters = ['names', 'authorityName',
                       'authorityIdentifier', 'kingdom',
                       'phylum', 'class', 'order',
                       'superFamily', 'family', 'genus',
                       'species', 'infraSpecies', 'hasRangeMap']
            query['filters'] = {}
            for f in filters:
                if self.request.params.get(f, None) is not None:
                    query['filters'][f] = self.request.params.get(f) 
            if self.request.params.get('simple', None) is not None:
                data = self.taxonomy.getsimple(query)
            else:
                data = self.taxonomy.getdata(query)
                
        self.response.out.write(simplejson.dumps(data))
        
    """
        
    def methods(self):
        out = {"methods":{
            "search": "provide a name string to search for",
            "rank": "indicate the name rank to search in, default genus species",
            "key": "provide the known key for a taxon 'animalia/rank/binomial'",
            "callback": "crossdomain callback name",
            "limit": "number of records to return",
            "offset": "number of records to skip, for paging",
            }
           }
        return out

    def fromKey(self, k):
        results = []
        start = time.time()
        key = db.Key.from_path('Species', k.lower())
        ent = Species.get(key)
        ele = k.split("/")
        e = {
             "rank": str(ele[-2]),
             "name": str(ele[-1]).replace("_", " "),
             "classification": simplejson.loads(ent.classification),
             "authority": simplejson.loads(ent.authority),
             "names": simplejson.loads(ent.names) #.replace('\\','')
            }
        results.append(e)
        t = int(1000 * (time.time() - start)) / 1000.0
        out = {"time":t, "items":results}
        return out

    def fromQuery(self, r, s, of, n, maps=False):
        start = time.time()
        results = []
        orderOn = r if r is not None else "genus"
        memk = "%s/%s/%s/%s/%s" % (r, s, of, n, str(maps))
        d = memcache.get(memk)
        if d is None:
            logging.info('Memcache miss on ' + memk)
            if r is None:
                q = SpeciesIndex.all(keys_only=True).filter("names =", s.lower()).order(orderOn)
            else:
                q = SpeciesIndex.all(keys_only=True).filter("%s =" % r, s.lower()).order(orderOn)
            if maps:
                q.filter('hasRangeMap =', maps)
            logging.info('query ' + str(q.__dict__))
            d = q.fetch(limit=n, offset=of)
        else:
            logging.info('Memcache hit on ' + memk)
        memcache.set(memk, d, 3000)
        ct = 0
        for key in d:
            ct += 1
            ent = db.get(key.parent())
            p = key.id_or_name().split('/')
            e = {"key_name" : key.name(),
                 "rank": str(p[-2]),
                 "name": str(p[-1]).replace("_", " "),
                 "classification": simplejson.loads(ent.classification),
                 "authority": ent.authority,
                 "names": simplejson.loads(ent.names) #.('\\','')
                }
            results.append(e)
        t = int(1000 * (time.time() - start)) / 1000.0
        out = {"time":t, "items":results, "offset":of, "limit":n}
        return out

    def get(self):
        self.post()

    def handle_data_source_request(self, returnJson=True):
        #tq = self.request.get('tq')
        #params = simplejson.loads(tq)
        #logging.info(str(params))
        limit = int(self.request.get('limit'))
        offset = int(self.request.get('offset'))
        gql = self.request.get('q').strip()
        rank = self.request.get('rank', None)
        key = self.request.get('key', None)
        maps = self.request.get('maps', False)
        if maps == 'false':
            maps = False
        if maps == 'true':
            maps = True
        else:
            maps = None
        logging.info('maps ' + str(maps))

        # Gets the data for the request:
        if key:
            out = self.fromKey(key)
        elif gql is not None:
            out = self.fromQuery(rank, gql, offset, limit, maps=maps)
            logging.info('GQL ' + gql)
        data = out.get('items')

        # TODO: how to handle 'classification' and 'names' in table format?
        # Right now just flattening classification and ignoring names...
        rows = []
        for rec in data:
            row = {"Accepted Name":rec["name"].capitalize(), "Author":rec["classification"]["author"]}
            taxonomy = "%s/%s/%s/%s/%s" % (rec["classification"]["kingdom"].capitalize(),
                                           rec["classification"]["phylum"].capitalize(),
                                           rec["classification"]["class"].capitalize(),
                                           rec["classification"]["order"].capitalize(),
                                           rec["classification"]["family"].capitalize())
            row["Kingdom/Phylum/Class/Order/Family"] = taxonomy

            names_csv = ""
            for name in rec["names"]:
                names_csv += name["name"].capitalize() + ","
            row["Synonyms CSV"] = names_csv[:-1]


            key_name = rec["key_name"]
            if TileSetIndex.get_by_key_name(key_name) is not None:
                row["Range Map"] = "<a href='/map/%s'>map</a>" % key_name
            else:
                row["Range Map"] = ""


            rows.append(row)

        # Builds DataTable for Google Visualization API:
        description = {"Accepted Name": ("string", "accepted name"),
                       "Author": ("string", "author"),
                       "Kingdom/Phylum/Class/Order/Family": ("string", "Kingdom/Pyhlum/Class/Family"),
                       "Synonyms CSV": ("string", "synonyms csv"),
                       "Range Map": ("string", "range map")}

        if len(rows) > 0:
            spec = rows[0]
            logging.info(type(spec))
            for key in spec.keys():
                description[key] = ("string", key)
            data_table = gviz_api.DataTable(description)
            data_table.LoadData(rows)
        else:
            data_table = gviz_api.DataTable({"GUID":("string", "")})

        # Sends the DataTable response:
        if returnJson:
            json = data_table.ToJSon()
            logging.info(json)
            self.response.out.write(json)
            return
        tqx = self.request.get("tqx")
        self.response.out.write(data_table.ToResponse(tqx=tqx))

    def simpleview(self, out):
        data = out.get("items")
        rows = []
        for rec in data:
            row = {"Name":rec["name"].capitalize(), "Author":rec["classification"]["author"]}
            taxonomy = "%s/%s/%s/%s/%s" % (rec["classification"]["kingdom"].capitalize(),
                                           rec["classification"]["phylum"].capitalize(),
                                           rec["classification"]["class"].capitalize(),
                                           rec["classification"]["order"].capitalize(),
                                           rec["classification"]["family"].capitalize())
            row["Taxonomy"] = taxonomy
            names_csv = ""
            for name in rec["names"]:
                names_csv += name["name"].capitalize() + ","
            row["Synonyms"] = names_csv[:-1]
            key_name = rec["key_name"]
            if TileSetIndex.get_by_key_name(key_name) is not None:
                row["Map"] = "<a href='/rangemap/%s'>map</a>" % key_name
            else:
                row["Map"] = ""
            rows.append(row)
        return rows

    def post(self):
        # Checks for and handles a Google Visualization data source request:
        tqx = self.request.get('tqx', None)
        if tqx is not None:
            logging.info(tqx)
            self.handle_data_source_request(returnJson=True)
            return

        # Handle a normal API request:
        cb = self.request.params.get('callback', None)
        if cb is not None:
            self.response.out.write("%s(" % cb)
        k = self.request.params.get('key', None)
        s = self.request.params.get('q', None)
        r = self.request.params.get('rank', None)
        n = int(self.request.params.get('limit', 10))
        of = int(self.request.params.get('offset', 0))

        self.response.headers['Content-Type'] = 'application/json'
        if k:
            out = self.fromKey(k)
        elif s is not None:
            out = self.fromQuery(r, s, of, n)
        else:
            out = self.methods()

        #self.response.out.write(simplejson.dumps(out, indent=4))
        data = self.simpleview(out)
        data = {"items":data}
        json = simplejson.dumps(data)
        json_clean = json.replace('\n', '')
        #json = json.replace("\\/", "/")
        self.response.out.write(json_clean);
        if cb is not None:
            self.response.out.write(")")
    """

class MetaDataDiscoveryHandler(webapp.RequestHandler):
    """Discovery API for metadata."""
    def get(self):
        q = self.request.get('q')
        if not q:
            self.error(404)
        keywords = [x.strip().lower() for x in q.split(',')]
        query = db.Query(MetaDataIndex, keys_only=True)
        for x in keywords:
            query.filter('keywords =', x)
        results = [simplejson.loads(md.object) for md in db.get([x.parent() for x in query])]
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(simplejson.dumps(results))
        
class MetadataHandler(webapp.RequestHandler):
    def get(self):
        key_name = self.request.params.get('key_name', 'ecoregion/wwf/AA0101') #or ecoregion, or protected area
        
        #key = ecoregion/wwf/AA0101
        fakeData = {
            "ecoregion/wwf/AA0101": {
                  "source":"World Wildlife Fund (WWF)",
                  "type":"Ecoregion",
                  "name":"Admiralty Islands lowland rain forests",
                  "description":None,
                  "temporal":{
                     "creation": "2001-03-02T00:00Z",
                     "upload": "2011-05-25T18:11Z",
                     "coverage": {
                         "start": "1990-01-01T00:00Z",
                         "end": "2020-01-01T00:00Z"
                     }
                  },
                  "storage":{
                     "location":"/ftp/ecoregion/shp/AA0101.shp",
                     "format":"esri-shape"
                  },
                  "spatial":{
                     "crs":{
                        "srs": "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs",
                        "extent":{
                           "text":"Global",
                           "coordinates":{
                              "0": 142.812,
                              "1": -2.57692,
                              "2": 147.879,
                              "3": -1.3724
                           }
                        },
                        "type":"vector",
                        "info": {
                           "resolution":{
                              "type": "derived",
                              "value":20,
                              "unit":"kilometer"
                           },
                        }
                     }
                  }
               },
            "range/mol/animalia/species/puma_concolor": {
                  "source":"IUCN Global Mammal Assessment",
                  "type":"Range",
                  "name":"Puma concolor",
                  "description":None,
                  "temporal":{
                     "creation": "2001-03-02T00:00Z",
                     "upload": "2011-05-25T18:11Z",
                     "coverage": {
                         "start": "1990-01-01T00:00Z",
                         "end": "2020-01-01T00:00Z"
                     }
                  },
                  "storage":{
                     "location":"/ftp/range/shp/animalia/species/puma_concolor.shp",
                     "format":"esri-shape"
                  },
                  "spatial":{
                     "crs":{
                        "srs": "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs",
                        "extent":{
                           "text":"Global",
                           "coordinates":{
                              "0": -135.365,
                              "1": -53.1062,
                              "2": -34.7901,
                              "3": 59.6663
                           }
                        },
                        "type":"vector",
                        "info": {
                           "resolution":{
                              "type": "derived",
                              "value":200,
                              "unit":"kilometer"
                           },
                        },
                     }
                  },
                "taxa": [
                    {"scope": "species",
                     "name": "Puma concolor"}
                  ]
               },
            "pa/wdpa/assemblage/AA0101": {
                  "source":"World Wildlife Fund (WWF)",
                  "type":"assemblage list",
                  "name":"Admiralty Islands lowland rain forests",
                  "description":None,
                  "temporal":{
                     "creation": "2001-03-02T00:00Z",
                     "upload": "2011-05-25T18:11Z",
                     "coverage": {
                         "start": "1990-01-01T00:00Z",
                         "end": "2020-01-01T00:00Z"
                     }
                  },
                  "storage":{
                     "location":"/ftp/ecoregion/assemblages/AA0101.csv",
                     "format":"csv"
                  },
                  "taxa": [
                    {"scope":"species",
                     "name":"Platymantis gilliardi",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Rana papua",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Kerivoula myrella",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Pipistrellus angulatus",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Echymipera kalubu",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Hipposideros cervinus",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Mosia nigrescens",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Pteropus hypomelanus",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Dobsonia anderseni",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Hipposideros diadema",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Pteropus admiralitatum",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Eugongylus rufescens",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Sphenomorphus jobiensis",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Tachybaptus novaehollandiae",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Anas superciliosa",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Nycticorax caledonicus",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Pandion haliaetus",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Haliastur indus",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Accipiter hiogaster",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Calidris ruficollis",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Sterna bergii",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Sterna albifrons",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Macropygia mackinlayi",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Chalcophaps stephani",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Caloenas nicobarica",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Ptilinopus superbus",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Ducula pistrinaria",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Ducula subflavescens",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Eclectus roratus",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Charmosyna placentis",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Cacomantis variolosus",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Ninox meeki",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Tyto novaehollandiae",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Aerodramus hirundinacea",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Aerodramus spodiopygius",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Alcedo atthis",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Todirhamphus saurophaga",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Merops ornatus",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Myzomela pammelaena",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Pachycephala pectoralis",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Rhipidura semirubra",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Monarcha infelix",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Coracina papuensis",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Aplonis cantoroides",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Aplonis metallica",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Zosterops hypoxanthus",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Burhinus giganteus",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Tiliqua gigas",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Candoia aspera",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Candoia carinata",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Miniopterus macrocneme",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Hipposideros calcaratus",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Macroglossus minimus",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Nyctimene albiventer",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Pteropus neohibernicus",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Rousettus amplexicaudatus",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Emballonura serii",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Nyctimene vizcaccia",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Rattus praetor",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Syconycteris australis",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Tachybaptus ruficollis",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Egretta sacra",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Ixobrychus flavicollis",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Aviceda subcristata",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Haliaeetus leucogaster",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Megapodius eremita",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Sterna sumatrana",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Macropygia amboinensis",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Reinwardtoena browni",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Gallicolumba beccarii",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Ptilinopus solomonensis",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Ducula spilorrhoa",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Micropsitta meeki",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Trichoglossus haematodus",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Cuculus saturatus",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Scythrops novaehollandiae",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Tyto manusi",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Aerodramus vanikorensis",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Ceyx lepidus",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Todirhamphus sanctus",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Pitta superba",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Philemon albitorques",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Rhipidura rufiventris",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Monarcha cinerascens",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Coracina tenuirostris",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Hirundo tahitica",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Nectarinia jugularis",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Bufo marinus",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Calidris acuminata",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Myiagra alecto",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Litoria thesaurensis",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Spilocuscus kraemeri",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Collocalia esculenta",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Sphenomorphus solomonis",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Podiceps cristatus",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Corvus corax",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Amphiuma tridactylum",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Boiga irregularis",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Dendrelaphis calligastra",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Gehyra oceanica",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Gekko vittatus",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Hemidactylus frenatus",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Lepidodactylus lugubris",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Lepidodactylus pulcher",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Nactus pelagicus",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Carlia fusca",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Emoia caeruleocauda",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Emoia cyanura",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Emoia jakati",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Emoia kordoana",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Emoia mivarti",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Geomyersia coggeri",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Lamprolepis smaragdina",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Lipinia noctua",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Sphenomorphus derroyae",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Tribolonotus brongersmai",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Acutotyphlops subocularis",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Litoria infrafrenata",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Discodeles vogti",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Ramphotyphlops depressus",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Ramphotyphlops flaviventer",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    },
                    {"scope":"species",
                     "name":"Stegonotus modestus",
                     "variables":{
                        "name":"introduced",
                        "value":False}
                    }
                  ]
               },
            }
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(simplejson.dumps(fakeData[key_name]))
        
               
        
    """
    def _getprops(self, obj):
        '''Returns a dictionary of entity properties as strings.'''
        dict = {}
        for key in obj.properties().keys():
            if key in ['extentNorthWest', 'extentSouthEast', 'status', 'zoom', 'dateLastModified', 'proj', 'type']:
                dict[key] = str(obj.properties()[key].__get__(obj, TileSetIndex))

        dict['mol_species_id'] = str(obj.key().name())
        return dict

    def get(self, class_, rank, species_id=None):
        self.post(class_, rank, species_id=None)

    def post(self, class_, rank, species_id=None):
        '''Gets a TileSetIndex identified by a MOL specimen id
        (/api/tile/metadata/specimen_id) or all TileSetIndex entities (/layers).
        '''
        if species_id is None or len(species_id) is 0:
            # Sends all metadata:
            self.response.headers['Content-Type'] = 'application/json'
            all = [self._getprops(x) for x in TileSetIndex.all()]
            # TODO: This response will get huge so we need a strategy here.
            self.response.out.write(simplejson.dumps(all))
            return

        species_key_name = os.path.join(class_, rank, species_id)
        metadata = TileSetIndex.get_by_key_name(species_key_name)
        if metadata:
            self.response.headers['Content-Type'] = 'application/json'
            self.response.out.write(simplejson.dumps(self._getprops(metadata)).replace("\\/", "/"))
        else:
            logging.error('No TileSetIndex for ' + species_key_name)
            self.error(404) # Not found
    """
class LayersHandler(BaseHandler):
    '''BaseHandler utility for backend to send information about updated 
       tilesets.
       
       Required query string parameters:
          
       Optional query string parameters:
    '''

    AUTHORIZED_IPS = ['128.138.167.165', '127.0.0.1', '71.202.235.132']

    def _update(self, metadata):

        errors = self._param('errors', required=False)
        if errors is not None:
            metadata.errors.append(errors)
            db.put(metadata)
            logging.info('Updated TileSetIndex with errors only: ' + errors)
            return

        enw = db.GeoPt(self._param('maxLat', type=float), self._param('minLon', type=float))
        ese = db.GeoPt(self._param('minLat', type=float), self._param('maxLon', type=float))
        metadata.extentNorthWest = enw
        metadata.extentSouthEast = ese
        metadata.dateLastModified = datetime.datetime.now()
        metadata.remoteLocation = db.Link(self._param('remoteLocation'))
        metadata.zoom = self._param('zoom', type=int)
        metadata.proj = self._param('proj')
        metadata.errors = []
        metadata.status = db.Category(self._param('status', required=False))
        metadata.type = db.Category(self._param('type', required=False))
        db.put(metadata)
        location = wsgiref.util.request_uri(self.request.environ).split('?')[0]
        self.response.headers['Location'] = location
        self.response.headers['Content-Location'] = location
        self.response.set_status(204) # No Content

    def _create(self, species_key_name):
        errors = self._param('errors', required=False)
        if errors is not None:
            db.put(TileSetIndex(key=db.Key.from_path('TileSetIndex', species_key_name),
                                errors=[errors]))
            logging.info('Created TileSetIndex with errors only')
            return

        species = Species.get_by_key_name(species_key_name)
        species_index = SpeciesIndex.get_by_key_name(species_key_name, parent=species)
        if species_index is not None:
            logging.info('Updating SpeciesIndex.hasRangeMap for %s' % species_key_name)
            species_index.hasRangeMap = True
            db.put(species_index)

        enw = db.GeoPt(self._param('maxLat', type=float), self._param('minLon', type=float))
        ese = db.GeoPt(self._param('minLat', type=float), self._param('maxLon', type=float))
        db.put(TileSetIndex(key=db.Key.from_path('TileSetIndex', species_key_name),
                            dateLastModified=datetime.datetime.now(),
                            remoteLocation=db.Link(self._param('remoteLocation')),
                            zoom=self._param('zoom', type=int),
                            proj=self._param('proj'),
                            extentNorthWest=enw,
                            extentSouthEast=ese,
                            status=db.Category(self._param('status', required=False)),
                            type=db.Category(self._param('type', required=False))))
        location = wsgiref.util.request_uri(self.request.environ)
        self.response.headers['Location'] = location
        self.response.headers['Content-Location'] = location
        self.response.set_status(201) # Created

    def _getprops(self, obj):
        '''Returns a dictionary of entity properties as strings.'''
        dict = {}
        for key in obj.properties().keys():
            dict[key] = str(obj.properties()[key].__get__(obj, TileSetIndex))
        dict['mol_species_id'] = str(obj.key().name())
        return dict

    def get(self, class_, rank, species_id=None):
        '''Gets a TileSetIndex identified by a MOL specimen id
        (/layers/specimen_id) or all TileSetIndex entities (/layers).
        '''
        if species_id is None or len(species_id) is 0:
            # Sends all metadata:
            self.response.headers['Content-Type'] = 'application/json'
            all = [self._getprops(x) for x in TileSetIndex.all()]
            # TODO: This response will get huge so we need a strategy here.
            self.response.out.write(simplejson.dumps(all))
            return

        species_key_name = os.path.join(class_, rank, species_id)
        metadata = TileSetIndex.get_by_key_name(species_key_name)
        if metadata:
            self.response.headers['Content-Type'] = 'application/json'
            self.response.out.write(simplejson.dumps(self._getprops(metadata)))
        else:
            logging.error('No TileSetIndex for ' + species_key_name)
            self.error(404) # Not found

    def put(self, class_, rank, species_id):
        '''Creates a TileSetIndex entity or updates an existing one if the
        incoming data is newer than what is stored in GAE.'''

        remote_addr = os.environ['REMOTE_ADDR']
        if not remote_addr in LayersHandler.AUTHORIZED_IPS:
            logging.warning('Unauthorized PUT request from %s' % remote_addr)
            self.error(401) # Not authorized
            return
        try:
            species_key_name = os.path.join(class_, rank, species_id)
            metadata = TileSetIndex.get_by_key_name(species_key_name)
            if metadata:
                self._update(metadata)
            else:
                self._create(species_key_name)
        except (BadArgumentError), e:
            logging.error('Bad PUT request %s: %s' % (species_key_name, e))
            self.error(400) # Bad request

class KeyHandler(webapp.RequestHandler):
    '''RequestHandler utility for backend to check if a layer is a valid
       layer to be tiling or analyzing. Used for dropping new layers into
       the pipeling.
       
       Required query string parameters:
          
       Optional query string parameters:
    '''
    def get(self, class_, rank, species_id=None):
        species_key_name = os.path.join(class_, rank, species_id)
        q = Species.get_by_key_name(species_key_name)
        if q:
            self.response.set_status(200)
        else:
            self.error(404)
            
class TileSetMetadata(webapp.RequestHandler):
    def _getprops(self, obj):
        '''Returns a dictionary of entity properties as strings.'''
        dict = {}
        for key in obj.properties().keys():
            if key in ['extentNorthWest', 'extentSouthEast', 'status', 'zoom', 'dateLastModified', 'proj', 'type']:
                dict[key] = str(obj.properties()[key].__get__(obj, TileSetIndex))
            """
            elif key in []:
                c = str(obj.properties()[key].__get__(obj, TileSetIndex))
                d = c.split(',')
                dict[key] = {"latitude":float(c[1]),"longitude":float(c[0])}
            """
        dict['mol_species_id'] = str(obj.key().name())
        return dict

    def get(self, class_, rank, sepecies_id=None):
        self.post(class_, rank, species_id)

    def post(self, class_, rank, species_id=None):
        '''Gets a TileSetIndex identified by a MOL specimen id
        (/api/tile/metadata/specimen_id) or all TileSetIndex entities (/layers).
        '''
        if species_id is None or len(species_id) is 0:
            # Sends all metadata:
            self.response.headers['Content-Type'] = 'application/json'
            all = [self._getprops(x) for x in TileSetIndex.all()]
            # TODO: This response will get huge so we need a strategy here.
            self.response.out.write(simplejson.dumps(all))
            return

        species_key_name = os.path.join(class_, rank, species_id)
        metadata = TileSetIndex.get_by_key_name(species_key_name)
        if metadata:
            self.response.headers['Content-Type'] = 'application/json'
            self.response.out.write(simplejson.dumps(self._getprops(metadata)).replace("\\/", "/"))
        else:
            logging.error('No TileSetIndex for ' + species_key_name)
            self.error(404) # Not found

class TilePngHandler(webapp.RequestHandler):
    """RequestHandler for map tile PNGs."""
    def __init__(self):
        super(TilePngHandler, self).__init__()
        self.ts = TileService()
    def get(self):
        #convert the URL route into the key (removing .png)
        url = self.request.path_info
        assert '/' == url[0]
        path = url[1:]
        (b1, b2, tileurl) = path.split("/", 2)
        tileurl = tileurl.split('.')[0]

        fullTest = False
        band = memcache.get("tile-%s" % tileurl)
        if band is None:
            tile = self.ts.tile_from_url(tileurl)
            if tile:
                band = tile.band

        if band is not None:
            memcache.set("tile-%s" % tileurl, band, 60)
            try:
                tmp = str(band)
            except:
                tmp = 0

            if cmp(tmp, 'f') == 0:
                self.redirect("/static/full.png")
            else:
                self.response.headers['Content-Type'] = "image/png"
                self.response.out.write(self.t.band)

class FindID(webapp.RequestHandler):
    def get(self, a, id):
        q = SpeciesIndex.all(keys_only=True).filter("authorityName =", a).filter("authorityIdentifier =", id)
        d = q.fetch(limit=2)
        if len(d) == 2:
            return "multiple matches"
        elif len(d) == 0:
            self.error(404)
        else:
            k = d[0]
            self.response.out.write(str(k.name()))

class RangeMapHandler(BaseHandler):
    '''Handler for rendering range maps based on species key_name.'''
    def get(self):
        self.push_html('range_maps.html')
   
class ColorImage(BaseHandler):
    """Handler for the search UI."""
    def get(self,name):
        
        r = int(self.request.get('r', 0))
        g = int(self.request.get('g', 0))
        b = int(self.request.get('b', 0))
        memk = "%s/%s/%s/%s" % (name, r, g, b)
        val = memcache.get(memk)
        if val is None:
            val = colorPng(name, r, g, b, isObj=False)
        memcache.set(memk, val, 60)
        
        # binary PNG data
        self.response.headers["Content-Type"] = "image/png"
        self.response.out.write(val)
        
"""
class EcoregionMetadata(webapp.RequestHandler):
    '''Method should be called as a first stop to any layer being loaded
       When executed, it also starts tiling zoom zero tiles for the layer
    '''
    def _getprops(self, obj):
        '''Returns a dictionary of entity properties as strings.'''
        dict = {}
        for key in obj.properties().keys():
            if key in ['extentNorthWest', 'extentSouthEast', 'dateCreated', 
                        'remoteLocation', 'ecoName', 'realm', 'biome', 'ecoNum', 
                        'ecoId', 'g200Region', 'g200Num', 'g200Biome', 'g200Stat']:
                dict[key] = str(obj.properties()[key].__get__(obj, Ecoregion))
        dict['ecoCode'] = str(obj.key().name())
        return dict

    def get(self, region_id=None):
        self.post(region_id)

    def post(self, region_id=None):
        metadata = Ecoregion.get_by_key_name(region_id)
        minx, maxy = obj.properties['extentNorthWest']
        maxx, miny = obj.properties['extentSouthEast']
        bboxurl = "http://mol.colorado.edu/layers/api/ecoregion/tilearea/" + \
                  "{code}?record_ids={code}&zoom={z}&lowx={minx}&lowy={miny}&highx={maxx}&highy={maxy}"
        bboxurl = bboxurl.replace("{code}",region_id)
        bboxurl = bboxurl.replace("{z}",0)
        bboxurl = bboxurl.replace("{minx}",minx)
        bboxurl = bboxurl.replace("{maxx}",maxx)
        bboxurl = bboxurl.replace("{miny}",miny)
        bboxurl = bboxurl.replace("{maxy}",maxy)
        rpc = urlfetch.create_rpc()
        urlfetch.make_fetch_call(rpc, bboxurl)
        if metadata:
            self.response.headers['Content-Type'] = 'application/json'
            self.response.out.write(simplejson.dumps(self._getprops(metadata)).replace("\\/", "/"))
        else:
            logging.error('No TileSetIndex for ' + record_id)
            self.error(404) # Not found
            
        result = rpc.get_result() #TODO: Aaron is this really necessary here?
"""

class EcoregionTileHandler(BaseHandler):
    def get(self, name):
        '''Handles a PNG map tile request according to the Google XYZ tile
        addressing scheme described here:
        
        Required query string parameters:
            z - integer zoom level
            y - integer latitude pixel coordinate
            x - integer longitude pixel coordinate
        '''
        name, ext = os.path.splitext(name)
        logging.info('Ecoregion collection name ' + name)
        # Returns a 404 if there's no TileSetIndex for the species id since we
        # need it to calculate bounds and for the remote tile URL:
        # TODO: create region metadata datastore
        #metadata = TileSetIndex.get_by_key_name(species_key_name)
        metadata = True
        # Returns a 404 if the requested region_id doesn't exist:
        if metadata is None:
            self.error(404) # Not found
            return
            
        # Returns a 400 if the required query string parameters are invalid:
        try:
            zoom = self._param('z')
            x = self._param('x')
            y = self._param('y')
        except (BadArgumentError), e:
            logging.error('Bad request params: ' + str(e))
            self.error(400) # Bad request
            return

        # Returns a 404 if the request isn't within bounds of the region:
        within_bounds = True; # TODO: Calculate if within bounds.
        if not within_bounds:
            self.error(404) # Not found
            return

        # Builds the tile image URL which is also the memcache key. It's of the
        # form: http://mol.colorado.edu/tiles/species_id/zoom/x/y.png
        #tileurl = metadata.remoteLocation
        tileurl ="http://mol.colorado.edu/layers/api/ecoregion/tile/{code}?zoom={z}&x={x}&y={y}"
        
        tileurl = tileurl.replace('{z}', zoom)
        tileurl = tileurl.replace('{x}', x)
        tileurl = tileurl.replace('{y}', y)
        tileurl = tileurl.replace('{code}', name)
        
        logging.info('Tile URL ' + tileurl)
        
        # Starts an async fetch of tile in case we get a memcache/datastore miss:
        # TODO: Optimization would be to async fetch the 8 surrounding tiles.
        rpc = urlfetch.create_rpc()
        urlfetch.make_fetch_call(rpc, tileurl)

        # Checks memcache for tile and returns it if found:
        memcache_key = "tileurl-%s" % tileurl
        
        r,g,b = None,None,None
        try:
            r = self._param('r')
            g = self._param('g')
            b = self._param('b')
            r,g,b = int(r),int(g),int(b)
            memk = "%s/%s/%s/%s" % (memcache_key, r, g, b)
            band = memcache.get(memk)
            band = None
            if band is not None:
                logging.info('Tile memcache hit: ' + memk)
                self.response.headers['Content-Type'] = "image/png"
                self.response.out.write(band)
                return
        except:
            pass
        
        band = memcache.get(memcache_key)
        if band is not None:
            logging.info('Tile memcache hit: ' + memcache_key)
            self.response.headers['Content-Type'] = "image/png"
            if b is not None:
                logging.info('colored')
                memk = "%s/%s/%s/%s" % (memcache_key, r, g, b)
                band = colorPng(band, r, g, b, isObj=True, memKey=memk)
            self.response.out.write(band)
            return
        
        # Checks datastore for tile and returns if found:
        """
        tile_key_name = os.path.join(species_key_name, zoom, y, x)
        tile = Tile.get_by_key_name(tile_key_name)
        if tile is not None:
            logging.info('Tile datastore hit: ' + tile_key_name)
            memcache.set(memcache_key, tile.band, 60)
            self.response.headers['Content-Type'] = "image/png"
            if b is not None:
                memk = "%s/%s/%s/%s" % (memcache_key, r, g, b)
                band = colorPng(tile.band, r, g, b, isObj=True, memKey=memk)
            self.response.out.write(tile.band)
            return
        """
        # Gets downloaded tile from async rpc request and returns it or a 404:
        try:
            result = rpc.get_result() # This call blocks.
            if result.status_code == 200:
                logging.info('Tile downloaded: ' + tileurl)
                band = result.content
                memcache.set(memcache_key, band, 60)
                self.response.headers['Content-Type'] = "image/png"
                if b is not None:
                    memk = "%s/%s/%s/%s" % (memcache_key, r, g, b)
                    band = colorPng(band, r, g, b, isObj=True, memKey=memk)
                self.response.out.write(band)
            else:
                logging.info('Status=%s, URL=%s' % (str(result.status_code), result.final_url))
                raise urlfetch.DownloadError('Bad tile result ' + str(result))
        except (urlfetch.DownloadError), e:
            logging.error('%s - %s' % (tileurl, str(e)))            
            self.error(404) # Not found

class EcoregionLayerSearch(BaseHandler):
    def get(self):
        self.post()
    def post(self):
        ecoCode = self._param('ecocode').strip()
        #er = Ecoregion.get_by_key_name(ecoCode)
        er = Ecoregion.get_or_insert(ecoCode)
        if True:
            nw = simplejson.loads(self._param('nw').replace("'",'"'))
            se = simplejson.loads(self._param('se').replace("'",'"'))
            
            url = "http://mol.colorado.edu/layers/api/ecoregion/tilearea/%s?zoom=0&lowx=%s&lowy=%s&highx=%s&highy=%s" % (ecoCode,nw['lon'],se['lat'],se['lon'],nw['lat'])
            logging.error(url)
            rpc = urlfetch.create_rpc()
            urlfetch.make_fetch_call(rpc, url)
            
            cl = simplejson.loads(self._param('clickables').replace("'",'"'))
            er.extentNorthWest = db.GeoPt(lat=nw['lat'],lon=nw['lon'])
            er.extentSouthEast = db.GeoPt(lat=se['lat'],lon=se['lon'])
            er.polyStrings = []
            ss = []
            ns = str(er.ecoName).split(' ')
            last = ""
            full = ""
            first = True
            for n in ns:
                n = n.lower()
                ss.append(n)
                subs = re.findall('\w+', n)
                if len(subs) > 1:
                    for s in subs:
                        ss.append(s)
                full = ' '.join([full, n])
                if first:
                    first = False
                else:
                    ss.append(last + ' ' + n)
                    ss.append(full)
                last = n
            
            for c in cl:
                poly = {"type": "bbox", 
                        "value": {
                            "nw": {"lat": c['nw']['lat'],"lon": c['nw']['lon']}, 
                            "se": {"lat": c['se']['lat'],"lon": c['se']['lon']}
                            }
                        }
                er.polyStrings.append(simplejson.dumps(poly))
            erL = EcoregionLayer.get_or_insert(ecoCode)
            erL.name=er.ecoName
            erL.id=ecoCode
            erL.ecoCodes = [ecoCode]
            erL.searchStrings = ss
            
            er.put()
            erL.put()
            
            result = rpc.get_result() # This call blocks.
            logging.error(result.status_code)
        else:
            logging.error(ecoCode)

application = webapp.WSGIApplication(
         [('/webapp', WebAppHandler),
         
          ('/data/points', PointsHandler), 
          ('/data/overview', OverviewImageHandler),
          ('/data/tile', TileHandler),
          ('/data/metadata', MetadataHandler),
          ('/data/metadata/discovery', MetaDataDiscoveryHandler),
          
          ('/search/taxonomy', TaxonomyHandler),
          
          ('/util/layers', LayersHandler), 
          ('/util/validkey', KeyHandler),

          ('/test/colorimage/([^/]+)', ColorImage),
          ('/test/findid/([^/]+)/([^/]+)', FindID),
          ('/test/tile/[\d]+/[\d]+/[\w]+.png', TilePngHandler),
          #('/test/ecoregion/tile/([\w]*.png)', EcoregionTileHandler),
          #('/test/ecoregion/search', EcoregionLayerSearch),
          #('/test/gbif', GBIFTest),
          #('/test/ecoregion/metadata/([\w]+)', EcoregionMetadata),
          ],
         debug=True)
         
def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
