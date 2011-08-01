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
from google.appengine.api import apiproxy_stub, apiproxy_stub_map, urlfetch, taskqueue
from google.appengine.api.datastore_file_stub import DatastoreFileStub
from google.appengine.ext import db
import logging
from math import ceil
from mol.db import MasterSearchIndex, Tile, MultiPolygon, MultiPolygonIndex, OccurrenceSetIndex, OccurrenceSet, MetaData
from xml.etree import ElementTree as etree
import datetime
import cStringIO
import os
import png
import re
import urllib
from google.appengine.api.datastore_errors import BadKeyError
from google.appengine.api import memcache
import StringIO
import simplejson

def colorPng(img, r, g, b, isObj=False):
    val = None
    if isObj:
        imt = png.Reader(bytes=img)
    else:
        imt=png.Reader(os.path.join(os.path.split(__file__)[0], 'images', img))
    im = imt.read()
    planes = im[3]['planes']
    itr = im[2]
    ar = list(itr)
    n = len(ar)
    row = 0
    
    while row < n:
        ct = planes
        col = len(ar[row])
        while ct <= col:
            if ar[row][ct-1]>0:
                ar[row][ct-4] = r
                ar[row][ct-3] = g
                ar[row][ct-2] = b
            ct+= planes
        ar[row] = tuple(ar[row])
        row+=1
    
    f = StringIO.StringIO()
    w = png.Writer(len(ar[0])/planes, len(ar), alpha=True)
    w.write(f, ar)
    val = f.getvalue()
    return val
    
def constant(f):
    def fset(self, value):
        raise SyntaxError
    def fget(self):
        return f()
    return property(fget, fset)

class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class TileError(Error):
    """Exception raised for errors related to Tile.

    Attributes:
      expr -- input expression in which the error occurred
      msg  -- explanation of the error
    """

    def __init__(self, expr, msg):
        self.expr = expr
        self.msg = msg

# ------------------------------------------------------------------------------
# TaxonomyService

class TaxonomyProvider(object):
    def __init__(self):
        pass
        
    def _key(self, k):
        raise NotImplementedError() 
        
    def _search(self, query):
        raise NotImplementedError() 
        
    def search(self, query):
        raise NotImplementedError() 
        
    def getdata(self, query):
        raise NotImplementedError() 

class TaxonomySearch(TaxonomyProvider):
    def __init__(self):
        super(TaxonomySearch, self).__init__()   
    
    def _key(self, k):
        key = db.Key.from_path('Species', k.lower())
        ent = Species.get(key)
        return [ent]
        
    def _search(self,query):
        
        res = []
        
        q = SpeciesIndex.all(keys_only=True)
              
        for a, b in query['filters'].items():
            q.filter("%s =" % str(a), b)
            
        if query.get('orderOn', None) is not None:
            q.order(orderOn['orderOn'])
        
        return q.fetch(query['limit'], query['offset'])
        
    def search(self, query):
        if query.get('key', None) is not None:
            result = self._key(query.get('key', False))
        else:
            params = {}
            params['limit'] = query.get('limit', 25)
            params['offset'] = query.get('offset', 25)
            
            params['filters'] = {}
            
            filterDict = ['names',
                          'authorityName',
                          'authorityIdentifier',
                          'kingdom',
                          'phylum',
                          'class',
                          'order',
                          'superFamily',
                          'family',
                          'genus',
                          'species',
                          'infraSpecies',
                          'hasRangeMap']
            
            fct = 0 #keeps the number of filters to the Datastore allowable 2
            for filter in filterDict:
                f = filter
                if f in ['class','order']:
                    f = f+"_"
                if query.get(f, None) is not None and fct < 2:
                    if f == 'hasRangeMap' and query.get(filter, 'true') == 'true':
                        params['filters'][f] = True
                    else:
                        params['filters'][f] = str(query.get(filter, ''))
                    fct+=1
            result = self._search()
        return result
        
    def getdata(self, query):
        s = self.search(query)
        out = []
        for ent in s:
            k = ent.key_name
            ele = k.split("/")
            e = {
                 "rank": str(ele[-2]),
                 "name": str(ele[-1]).replace("_", " "),
                 "classification": simplejson.loads(ent.classification),
                 "authority": simplejson.loads(ent.authority),
                 "names": simplejson.loads(ent.names) #.replace('\\','')
                }
            out.append(e)
        return out
        
    def getsimple(self, query):
        s = self.search(query)
        out = []
        for ent in s:
            k = ent.key_name
            ele = k.split("/")
            e = {
                 "name": str(ele[-1]).replace("_", " "),
                 "rank": str(ele[-2]),
                 "authority": simplejson.loads(ent.authority),
                }
            out.append(e)
        return out
        
    
# ------------------------------------------------------------------------------
# LayerService

class LayerType(object):
    @constant
    def POINTS():
        return 'points'
    @constant
    def RANGE():
        return 'range'
    @constant
    def POLYGON():
        return 'polygon'
    @constant
    def ECOREGION():
        return 'ecoregion'

class LayerSource(object):
    @constant
    def GBIF():
        return 'gbif'
    @constant
    def MOL():
        return 'mol'
    @constant
    def WWF():
        return 'wwf'
    
class LayerService(object):

    def __init__(self):
        self.providers = {LayerSource.GBIF: GbifLayerProvider()}
        
    def search(self, query):
        sources = query.get('sources', [])
        types = query.get('types', [])
        providers = self._get_providers(sources, types)        
        self.results = []
        rpcs = []

        for provider in providers:
            url = provider.geturl(query)
            rpc = urlfetch.create_rpc()
            rpc.callback = self._create_layer_search_callback(provider, rpc)
            urlfetch.make_fetch_call(rpc, url)
            rpcs.append(rpc)
        
        for rpc in rpcs:
            rpc.wait()
        return self.results
    
    def _get_providers(self, sources, types):
        return [self.providers[LayerSource.GBIF]]

    def _handle_layer_search_callback(self, provider, rpc):
        profile = provider.getprofile(rpc.get_result())
        self.results.append(profile)

    def _create_layer_search_callback(self, provider, rpc):
        return lambda: self._handle_layer_search_callback(provider, rpc)

class MasterTermSearch(object):
    def __init__(self, query, gbifquery=True):
        self.cachetime = 6000
        self.query = query
        self.types = {}
        self.sources = {}
        self.layers = {}
        self.names = {}
        self.gbifnames = None
        self.keys = None
        self.rpc = None
        self.api_results = None
        self.cachetime = 6000
        self.mmc = None
        self.mmc_result = None
        self.memkey = "MasterTermSearch/%s/%s/%s" % (self.query['term'],self.query['limit'],self.query['offset'])
        self.gbifmemkey = "GBIF/namesearch/%s/%s/%s" % (self.query.get('term'),self.query.get('limit', 10),self.query.get('start', 0))
        self.gbifquery = gbifquery #tells service whether or not to include GBIF results
        self.apimemkey = "MTSAPI/%s/%s/%s" % (self.query['term'],self.query['limit'],self.query['offset'])
        
    def _addresult(self, category, source, name, subname, info, key_name, ct):
        if category not in self.types.keys():
            self.types[category] = {"names": [],"sources": [], "layers": []}
        if source not in self.sources.keys():
            self.sources[source] = {"names": [],"types": [],"layers": []}
        if name not in self.names.keys():
            self.names[name] = {"sources": [],"types": [],"layers": []}
                
        if name not in self.types[category]["names"]:
            self.types[category]["names"].append(name)
        if name not in self.sources[source]["names"]:
            self.sources[source]["names"].append(name)
        
        if source not in self.types[category]["sources"]:
            self.types[category]["sources"].append(source)
        if source not in self.names[name]["sources"]:
            self.names[name]["sources"].append(source)
            
        if category not in self.sources[source]["types"]:
            self.sources[source]["types"].append(category)
        if category not in self.names[name]["types"]:
            self.names[name]["types"].append(category)
            
        self.types[category]["layers"].append(ct)
        self.sources[source]["layers"].append(ct)
        self.names[name]["layers"].append(ct)
        
        self.layers[ct] = {
            "name": name,
            "name2": subname,
            "source": source,
            "type": category,
            "info": info,
            "key_name": key_name
            }
                
    def _memcache(self):
        if self.mmc is None:
            self.mmc = []
            self.mmc.append(self.memkey)
            if self.gbifquery:
                self.mmc.append(self.gbifmemkey)
            self.mmc_result = memcache.get_multi(self.mmc)
            
    def gbifnamesearch(self):
        self._memcache()
        if self.gbifquery:
            params = urllib.urlencode({
                    'maxResults': self.query.get('gbifLimit', 150),
                    'startIndex': self.query.get('gbifOffset', 0),
                    'query': self.query.get('term'),
                    'returnType': 'nameId'})
            url = 'http://data.gbif.org/species/nameSearch?%s' % params
            self.rpc = urlfetch.create_rpc()
            urlfetch.make_fetch_call(self.rpc, url)
            
    def gbifresults(self):
        if self.gbifquery:      
            if self.gbifmemkey in self.mmc_result:
                self.gbifnames = self.mmc_result[self.gbifmemkey]
            if self.gbifnames is None:
                result = self.rpc.get_result()
                self.gbifnames = []
                ct = 0
                for i in result.content.split('\n'):
                    i = i.strip().split('\t')
                    if len(i)>1:
                        gname = i[1].strip()
                        """Filter out subspecies and virus from GBIF results"""
                        if 'subsp.' not in gname and 'virus' not in gname:
                            self.gbifnames.append({'name': gname, 'subname': 'GBIF Points', 
                                                   'category': 'points', 'source': 'GBIF', 'info': None,
                                                   'key_name': "points/gbif/%s" % i[0].strip()})
                            ct+=1
                memcache.set(self.gbifmemkey, self.gbifnames, 10*self.cachetime)
            return self.gbifnames
        else:
            return []
            
    def search(self):
        self._memcache()      
        if self.memkey in self.mmc_result:
            self.keys = self.mmc_result[self.memkey]
        else:
            osi = MasterSearchIndex.all(keys_only=True)
            osi.filter("term =",str(self.query['term']).lower()).order("-rank")
            res = osi.fetch(limit=self.query["limit"],offset=self.query["offset"])
            self.keys = [i.parent() for i in res]
            memcache.set(self.memkey, self.keys, self.cachetime)
            
    def api_format(self):
        self.api_results = memcache.get(self.apimemkey)
        if self.api_results is None:
            self.gbifnamesearch()
            self.search()
            gbifnames = self.gbifresults()
            delcache = False
            kct = -1
            ct = 0
            for r in db.get(self.keys):
                if r is not None:
                    self._addresult(r.category, r.source, r.name, r.subname, r.info, r.key().name(), ct)
                
                    ctg = (ct+1)%8
                    ct+=1
                    if (ctg==0 or ct==4) and len(gbifnames)>0:
                        cur = gbifnames.pop(0)
                        self._addresult(cur["category"], 
                                        cur["source"], 
                                        cur["name"], 
                                        cur["subname"], 
                                        cur["info"], 
                                        cur["key_name"], 
                                        ct)
                        ct+=1
                    kct += 1
                else:
                    rk = self.keys[kct]
                    db.delete(MasterSearchIndex.all(keys_only=True).ancestor(rk).fetch(100))
                    db.delete(MultiPolygonIndex.all(keys_only=True).ancestor(rk).fetch(100))
                    db.delete(OccurrenceSetIndex.all(keys_only=True).ancestor(rk).fetch(100))
                    delcache = True
            if delcache:
                memcache.delete(self.memkey)
            while len(gbifnames) > 0:
                cur = gbifnames.pop(0)
                self._addresult(cur["category"], 
                                cur["source"], 
                                cur["name"], 
                                cur["subname"], 
                                cur["info"], 
                                cur["key_name"], 
                                ct)
                ct+=1
        
            self.api_results = {"query": self.query, "types": self.types, 
                   "sources": self.sources, "layers": self.layers,
                   "names": self.names}
            memcache.set(self.apimemkey, self.api_results, self.cachetime)
        return self.api_results

class MetadataProvider(object):
    def __init__(self):
        pass
    def getitem(self, query):
        self.query = query
        key_name = self.query.get('key_name')

#        fakeItem = {"collectionKey": "collection/ecoregion/wwf/latest", "name": "Banda Sea Islands moist deciduous forests", "temporal": {"coverage": {"start": None, "end": None}}, "storage": {"format": "Esri Shapefile", "uploadDate": "2011-06-03 12:35:08.701490", "location": "/ftp/ecoregion/shp/AA0102.shp"}, "source": "World Wildlife Fund (WWF)", "spatial": {"crs": {"info": {"resolution": {"type": None, "value": None, "unit": None}}, "srs": "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs", "type": "multipolygon", "extent": {"text": None, "coordinates": {"1": -8.34339466646, "0": 127.139602677, "3": -5.27165698158, "2": 133.197601577}}, "format": "vector"}}, "creationDate": None, "type": "Ecoregion", "variables": [{"name": "eco_code", "value": "AA0102"}], "description": None}

        # The fakeWWFEcoregionSetCollectionMetadata needs to have information about where the checklists come from.
        fakeWWFEcoregionSetCollectionMetadata = {"source":"World Wildlife Fund (WWF)",  "type":"Bioinventory",  "name":"World Ecoregions",  "description":"The WWF's Conservation Science Program (CSP) has developed a biogeographic regionalization of the Earth's terrestrial biodiversity. WWF termed the biogeographic units ecoregions, defined as relatively large units of land or water containing distinct assemblages of natural communities sharing a large majority of species, dynamics, and environmental conditions. Ecoregions represent the original distribution of distinct assemblages of species and communities.",  "url":"http://www.worldwildlife.org/science/ecoregions/item1267.html",  "agreements":{},  "creationDate": "2001",  "uploadDate": str(datetime.datetime.now()),  "changeDate": "2001",  "allowed_uses":{"visualization": "unknown",  "download": "unknown",},  "references":{"0":{"authors":"Olson, D.M.; Dinerstein, E.; Wikramanayake, E.; Burgess, N.; Powell, G.; Underwood, E. C.; D'Amico, J.; Itoua, I.; Strand, H.; Morrison, J.; Loucks, C.; Allnutt, T.; Ricketts, T.H.; Kura, Y.; Wettengel, W.; Kassem,K.",  "year":2001,  "publication":"BioScience, Volume 51, Issue 11, p.933-938",  "title":"Terrestrial ecoregions of the world: a new map of life on earth"}}, "spatial":{"crs":{"srs": "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs", "extent":{"text":"Global",  "coordinates":{"0": -90.0, "1": -180.0, "2": 90.0, "3": 180.0}}, "format": "vector", "type": "multipolygon", "info": {"resolution": {"type": None,  "value": None,  "unit": None}},},}}
        fakeWWFEcoregionCollectionMetadata = {"source":"World Wildlife Fund (WWF)",  "type":"Ecoregion",  "name":"World Ecoregions",  "description":"The WWF's Conservation Science Program (CSP) has developed a biogeographic regionalization of the Earth's terrestrial biodiversity. WWF termed the biogeographic units ecoregions, defined as relatively large units of land or water containing distinct assemblages of natural communities sharing a large majority of species, dynamics, and environmental conditions. Ecoregions represent the original distribution of distinct assemblages of species and communities.",  "url":"http://www.worldwildlife.org/science/ecoregions/item1267.html",  "agreements":{},  "creationDate": "2001",  "uploadDate": str(datetime.datetime.now()),  "changeDate": "2001",  "allowed_uses":{"visualization": "unknown",  "download": "unknown",},  "references":{"0":{"authors":"Olson, D.M.; Dinerstein, E.; Wikramanayake, E.; Burgess, N.; Powell, G.; Underwood, E. C.; D'Amico, J.; Itoua, I.; Strand, H.; Morrison, J.; Loucks, C.; Allnutt, T.; Ricketts, T.H.; Kura, Y.; Wettengel, W.; Kassem,K.",  "year":2001,  "publication":"BioScience, Volume 51, Issue 11, p.933-938",  "title":"Terrestrial ecoregions of the world: a new map of life on earth"}}, "spatial":{"crs":{"srs": "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs", "extent":{"text":"Global",  "coordinates":{"0": -90.0, "1": -180.0, "2": 90.0, "3": 180.0}}, "format": "vector", "type": "multipolygon", "info": {"resolution": {"type": None,  "value": None,  "unit": None}},},}}
        # The fakeGBIFCollectionMetadata needs to have information about the taxon and the original sources.
        fakeGBIFCollectionMetadata = { 
            "source":"Data Publishers of the Global Biodiversity Information Facility (GBIF)", 
            "type":"Occurrence Points", 
            "name":"Global Biodiversity Information Facility", 
            "description":"Occurrence records accessed from various data publishers through the aggregate index of the Global Biodiversity Information Facility",
            "url":"",
            "agreements":{},
            "creationDate":str(datetime.datetime.now()),
            "uploadDate":str(datetime.datetime.now()),
            "changeDate":str(datetime.datetime.now()),
            "allowed_uses":{
                  "visualization": "unknown",
                  "download": "unknown",
                 },
             "spatial":{
                "crs":{
                   "srs": "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs",
                   "extent":{
                      "text":"Global",
                      "coordinates":{
                         "0": -90.0,
                         "1": -180.0,
                         "2": 90.0,
                         "3": 180.0
                      }
                   },
                   "format": "vector",
                   "type": "multipolygon",
                   "info": {
                        "resolution": {
                            "type": None,
                            "value": None,
                            "unit": None
                        }
                    },
                },
            },
            
        }        
        fakeJetzRangeCollectionMetadata = {
          "source":"Walter Jetz Lab",
          "type":"Range",
          "name":"Digital Distribution Maps of Birds",
          "description":"This dataset contains distribution information of species assessed for The IUCN Red List of Threatened Species. The maps are developed as part of a comprehensive assessment of global biodiversity in order to highlight taxa threatened with extinction, and thereby promote their conservation.",
          "url":"http://www.iucnredlist.org/spatial-data/2010.4/GISData/RLSpatial_metadata_Oct2010.pdf",
          "agreements":{},
          "creationDate": "2009-11",
          "uploadDate": str(datetime.datetime.now()),
          "changeDate": "2010-10",
          "allowed_uses":{
              "visualization": "unknown",
              "download": "unknown",
             },
             "spatial":{
                "crs":{
                   "srs": "+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext +over +no_defs",
                   "extent":{
                      "text":"Global",
                      "coordinates":{
                         "0": -90.0,
                         "1": -180.0,
                         "2": 90.0,
                         "3": 180.0
                      }
                   },
                   "format": "vector",
                   "type": "multipolygon",
                   "info": {
                        "resolution": {
                            "type": None,
                            "value": None,
                            "unit": None
                        }
                    },
                },
            },
           "taxa": [
                {"scope": "class",
                 "name": "Aves"}
           ]
        }
         
        fakeWDPACollectionMetadata = {
          "source":"IUCN and UNEP",
          "type":"Bioinventory",
          "name":"World Database on Protected Areas",
          "description":"An interactive database for protected areas worldwide, reconciling governmental, expert and general public opinions on protected areas. It encompasses the World Database on Protected Areas and provides a platform for the protected area constituency.",
          "url":"http://www.protectedplanet.net/about",
          "agreements":{},
          "creationDate": "2010",
          "uploadDate": str(datetime.datetime.now()),
          "changeDate": "2010",
          "allowed_uses":{
              "visualization": "unknown",
              "download": "unknown",
             },
              "references":{
                 "0":{
                    "authors":"IUCN and UNEP",
                    "year":2010,
                    "publication":"UNEP-WCMC. Cambridge, UK. www.protectedplanet.net",
                    "title":"The World Database on Protected Areas (WDPA)"
                    }
                 },
             "spatial":{
                "crs":{
                   "srs": "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs",
                   "extent":{
                      "text":"Global",
                      "coordinates":{
                         "0": -90.0,
                         "1": -180.0,
                         "2": 90.0,
                         "3": 180.0
                      }
                   },
                   "format": "vector",
                   "type": "multipolygon",
                   "info": {
                        "resolution": {
                            "type": None,
                            "value": None,
                            "unit": None
                        }
                    },
                },
            },
        }
        
        fakeIUCNRangeCollectionMetadata = {
          "source":"International Union for Conservation of Nature (IUCN)",
          "type":"Range",
          "name":"Digital Distribution Maps of The IUCN Red List of Threatened Species",
          "description":"This dataset contains distribution information of species assessed for The IUCN Red List of Threatened Species. The maps are developed as part of a comprehensive assessment of global biodiversity in order to highlight taxa threatened with extinction, and thereby promote their conservation.",
          "url":"http://www.iucnredlist.org/spatial-data/2010.4/GISData/RLSpatial_metadata_Oct2010.pdf",
          "agreements":{},
          "creationDate": "2009-11",
          "uploadDate": str(datetime.datetime.now()),
          "changeDate": "2010-10",
          "allowed_uses":{
              "visualization": "unknown",
              "download": "unknown",
             },
             "spatial":{
                "crs":{
                   "srs": "+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext +over +no_defs",
                   "extent":{
                      "text":"Global",
                      "coordinates":{
                         "0": -90.0,
                         "1": -180.0,
                         "2": 90.0,
                         "3": 180.0
                      }
                   },
                   "format": "vector",
                   "type": "multipolygon",
                   "info": {
                        "resolution": {
                            "type": None,
                            "value": None,
                            "unit": None
                        }
                    },
                },
            },
           "taxa": [
                {"scope": "class",
                 "name": "Mammalia"},
                {"scope": "class",
                 "name": "Amphibia"},
                {"scope": "class",
                 "name": "Reptilia"}
           ]
        }
        # This is a hack. ecoregions bulkloaded with parent key stored in MetaData.parentKey
        # while ranges bulkloaded with parent key encoded in key.
        # Thank JRW for these comments!

        if key_name.__contains__('range'):
            md = db.get(db.Key.from_path('MultiPolygon', key_name, 'MetaData', key_name))
            if md is not None:                
                data = md.object
                logging.info('MD.OBJECT=%s' % data)
                return dict(
                    key_name=key_name,
                    data=simplejson.loads(data))
        else:
            n = MetaData.get_by_key_name(key_name)
            if n is not None:
                data = n.object
                return dict(
                    key_name=key_name,
                    data=simplejson.loads(data))
#        if key_name.__contains__('ecoregion'):
#            n = MetaData.get_by_key_name(key_name)
#            if n is not None:
#                data = n.object
#                return dict(
#                    key_name=key_name,
#                    data=simplejson.loads(data))
#        elif key_name.__contains__('range'):
#            md = db.get(db.Key.from_path('MultiPolygon', key_name, 'MetaData', key_name))
#            if md is not None:                
#                data = md.object
#                logging.info('MD.OBJECT=%s' % data)
#                return dict(
#                    key_name=key_name,
#                    data=simplejson.loads(data))

        # Even worse hack
        if key_name.__contains__('collection/ecoregion-group'):
            data = fakeWWFEcoregionSetCollectionMetadata
        elif key_name.__contains__('collection/ecoregion'):
            data = fakeWWFEcoregionCollectionMetadata
        elif key_name.__contains__('collection/range/mol'):
            data = fakeIUCNRangeCollectionMetadata
        elif key_name.__contains__('collection/pa-group/wdpa-group'):
            data = fakeWDPACollectionMetadata
        elif key_name.__contains__('collection/pa/wdpa'):
            data = fakeWDPACollectionMetadata
        elif key_name.__contains__('collection/range/jetz'):
            data = fakeJetzRangeCollectionMetadata
        elif key_name.__contains__('collection/points/gbif'):
            data = fakeGBIFCollectionMetadata
        else:
            data = {
                    "source":"Map of Life",
                    "type": key_name
            }
        return {"key_name": key_name,
                "data": data}
            
        
class LayerProvider(object):
    """An abstract base class for the Layer service."""
        
    def __init__(self, types, sources):
        self._types = types    
        self._sources = sources

    def getdata(self, query):
        raise NotImplementedError()    

    def getprofile(self, data):
        raise NotImplementedError()    

    def geturl(self, query):
        return None

    def getTypes(self):
        return self._types
    types = property(getTypes)

    def getSources(self):
        return self._sources
    sources = property(getSources)

class OverviewImageProvider(object):
    def __init__(self, params):
        self.key_name = params.get('key_name')
        self.w = params.get('width')
        self.h = params.get('height')
        self.img = None
        self.cachetime = 60000   
        self.memkey = None
        self.url = None
        self.backend = "http://96.126.97.48/layers"
        #self.backend = "http://127.0.0.1:5003/layers"
        
        d = self.key_name.split('/', 2)
        self.datatype, self.source, self.id = d[0].lower(),d[1],d[2]
        
    def geturl(self):
        params = urllib.urlencode({
                'w': self.w,
                'h': self.h,
                'id': self.id}) 
        self.url = self.backend + '/api/overview/%s?%s' % (self.datatype,params)
        self.memkey = self.url
        
    def getimg(self):
        
        rpc = urlfetch.create_rpc()
        self.geturl()
        urlfetch.make_fetch_call(rpc, self.url)
        self.img = None #memcache.get(self.memkey)
        if self.img is None:
            try:
                result = rpc.get_result() 
                if result.status_code == 200:
                    self.img = result.content
                    memcache.set(self.memkey,self.img,self.cachetime)
            except (urlfetch.DownloadError), e:
                logging.error('MOL overview request: %s (%s)' % (rpc, str(e)))
        
    
class GbifLayerProvider(LayerProvider):
    
    def __init__(self):
        types = [LayerType.POINTS]
        sources = [LayerSource.GBIF]
        super(GbifLayerProvider, self).__init__(types, sources)   
        self.cachetime = 60000   
        self.memkey = None
    
    def geturl(self, query):
        params = urllib.urlencode({
                'format': query.get('format', 'darwin'),
                'coordinateStatus': True,
                'maxResults': query.get('limit', 150),
                'startIndex': query.get('start', 0),
                'scientificname': query.get('layerName')})
        url = 'http://data.gbif.org/ws/rest/occurrence/list?%s' % params
        self.memkey = url
        return url

    def getdata(self, query):
        rpc = urlfetch.create_rpc(deadline=10)
        url = self.geturl(query)
        urlfetch.make_fetch_call(rpc, url)
        self.gbifjson = memcache.get(self.memkey)
        if self.gbifjson is None:
            try:
                result = rpc.get_result() 
                if result.status_code == 200:
                    self.gbifjson = self.xmltojson(result.content, url)
                    memcache.set(self.memkey,self.gbifjson,self.cachetime)
            except (urlfetch.DownloadError), e:
                logging.error('GBIF request: %s (%s)' % (rpc, str(e)))
                #TODO issue a redirect to same url but asking for fewer records
        return self.gbifjson
            
    def xmltojson(self,xmldata,url):
        NSXML = "http://portal.gbif.org/ws/response/gbif"
        TOXML = "http://rs.tdwg.org/ontology/voc/TaxonOccurrence#"
        xml = etree.iterparse(cStringIO.StringIO(xmldata), ("start", "end"))
        out = {"publishers":[]}
        provider, resource, occurrence = {"resources": []}, {"occurrences": []}, {"coordinates": {"coordinateUncertaintyInMeters": None,"decimalLongitude": None,"decimalLatitude": None}}
        p, r, o = True, False, False
        pct, rct, oct = 0, 0, 0
        for action, element in xml:
            #logging.info('element.text:%s, type:%s ' % (element.text, type(element.text)))
            if "{%s}TaxonOccurrence" % TOXML == element.tag:
                if action=="start":
                    p, r, o = False, False, True
                    #logging.error(o)
                elif action=="end":
                    oct+=1
                    resource['occurrences'].append(occurrence)
                    occurrence = {"coordinates": {"coordinateUncertaintyInMeters": None,"decimalLongitude": None,"decimalLatitude": None}}

            elif "{%s}dataResource" % NSXML == element.tag:
                if action=="start":
                    p, r, o = False, True, False
                elif action=="end":
                    rct+=1
                    provider['resources'].append(resource)
                    resource = {'occurrences':[]}

            elif "{%s}dataProvider" % NSXML == element.tag:
                if action=="start":
                    p, r, o = True, False, False
                elif action=="end":
                    pct+=1
                    out["publishers"].append(provider)
                    provider = {"resources": []}

            elif p or r:
                if "{%s}name" % NSXML == element.tag:
                    if p:
                        provider['name'] = element.text
                    elif r:
                        resource['name'] = element.text
            elif o:
                if element.tag in ["{%s}decimalLatitude" % TOXML, "{%s}decimalLongitude" % TOXML]:
                    try:
                        occurrence["coordinates"][str(element.tag).split("}")[1]] = float(element.text)
                    except:
                        occurrence["coordinates"][str(element.tag).split("}")[1]] = None
                elif "{%s}coordinateUncertaintyInMeters" % TOXML == element.tag:
                    try:
                        occurrence["coordinates"]["coordinateUncertaintyInMeters"] = float(element.text)
                        assert occurrence["coordinates"]["coordinateUncertaintyInMeters"] > 0
                    except:
                        occurrence["coordinates"]["coordinateUncertaintyInMeters"] = None
        logging.error(oct)
        return {"source": "GBIF", "sourceUrl": url, "accessDate": str(datetime.datetime.now()), "totalPublishers": pct, "totalResources": rct, "totalRecords": oct, "records": out}
        
    def getprofile(self, query, url, content):
        return {    
            "query": {
                "search": query.get('sciname'),
                "offset": query.get('start', 0),
                "limit": query.get('limit', 400),
                "source": url,
                "type": "points",
                "advancedOptions": {"coordinatestatus": True}
                },
            
            "types": {
                "points": {
                    "names": [query.get('sciname')],
                    "sources": ["GBIF"],
                    "layers": [0]
                    }      
                },
            
            "sources": {
                "GBIF": {
                    "names": [query.get('sciname')],
                    "types": ["points"],
                    "layers": [0]
                    }, 
                },
            
            "names": {
                query.get('sciname'): {
                    "sources": ["GBIF"],
                    "layers": [0],
                    "types": ["points"]
                    },
                },
            
            "layers": {
                0 : {"name" : query.get('sciname'),
                     "name2" : query.get('name2'), 
                     "source": "GBIF",
                     "type": "points",
                     "count": content["records"]
                    } 
                }
            }

class EcoregionLayerProvider(LayerProvider):
    
    def __init__(self):
        types = [LayerType.ECOREGION]
        sources = [LayerSource.WWF]
        super(GbifLayerProvider, self).__init__(types, sources)        
        
    def getdata(self, query):
        """TODO: add a new table to datastore that maps species
            to ecoregion ids"""
        return {
            "source": "WWF",
            "sourceUrl": "http://mappinglife.org/path/to/data/for/puma_concolor",
            "totalRegions": 202,
            "accessDate": str(datetime.datetime.now()),
            "regions": {
                "NA0417": {"introduced": False, "name": "Willamette Valley forests"},
                "NA0505": {"introduced": False, "name": "Blue Mountains forests"},
                "NA0506": {"introduced": False, "name": "British Columbia mainland coastal forests"},
                "NA0507": {"introduced": False, "name": "Cascade Mountains leeward forests"},
                "NA0508": {"introduced": False, "name": "Central and Southern Cascades forests"},
                "NA0511": {"introduced": False, "name": "Colorado Rockies forests"},
                "NA0519": {"introduced": False, "name": "Northern California coastal forests"},
                "NA0526": {"introduced": False, "name": "Sierra Juarez and San Pedro Martir pine-oak forests"},
                "NA0803": {"introduced": False, "name": "Central and Southern mixed grasslands"},
                "NA0808": {"introduced": False, "name": "Montana Valley and Foothill grasslands"},
                "NA0813": {"introduced": False, "name": "Palouse grasslands"},
                "NA0814": {"introduced": False, "name": "Texas blackland prairies"},
                "NA1201": {"introduced": False, "name": "California coastal sage and chaparral"},
                "NA1304": {"introduced": False, "name": "Colorado Plateau shrublands"},
                "NA1305": {"introduced": False, "name": "Great Basin shrub steppe"},
                "NA1306": {"introduced": False, "name": "Gulf of California xeric scrub"},
                "NA1308": {"introduced": False, "name": "Mojave desert"},
                "NA1311": {"introduced": False, "name": "Tamaulipan matorral"},
                "NT0102": {"introduced": False, "name": "Atlantic Coast restingas"},
                "NT0103": {"introduced": False, "name": "Bahia coastal forests"},
                "NT0104": {"introduced": False, "name": "Bahia interior forests"},
                "NT0106": {"introduced": False, "name": "Caatinga Enclaves moist forests"},
                "NT0107": {"introduced": False, "name": "Caqueta moist forests"},
                "NT0108": {"introduced": False, "name": "Catatumbo moist forests"},
                "NT0111": {"introduced": False, "name": "Central American Atlantic moist forests"},
                "NT0121": {"introduced": False, "name": "Eastern Cordillera real montane forests"},
                "NT0122": {"introduced": False, "name": "Eastern Panamanian montane forests"},
                "NT0124": {"introduced": False, "name": "Guianan Highlands moist forests"},
                "NT0130": {"introduced": False, "name": "Isthmian-Pacific moist forests"},
                "NT0132": {"introduced": False, "name": "Japur-Solimoes-Negro moist forests"},
                "NT0135": {"introduced": False, "name": "Madeira-Tapajs moist forests"},
                "NT0137": {"introduced": False, "name": "Magdalena-Urab moist forests"},
                "NT0140": {"introduced": False, "name": "Mato Grosso seasonal forests"},
                "NT0148": {"introduced": False, "name": "Pantanos de Centla"},
                "NT0151": {"introduced": False, "name": "Pernambuco coastal forests"},
                "NT0157": {"introduced": False, "name": "Purus-Madeira moist forests"},
                "NT0162": {"introduced": False, "name": "Sierra Madre de Chiapas moist forests"},
                "NT0163": {"introduced": False, "name": "Solimes-Japur moist forests"},
                "NT0165": {"introduced": False, "name": "Southern Andean Yungas"},
                "NT0166": {"introduced": False, "name": "Southwest Amazon moist forests"},
                "NT0167": {"introduced": False, "name": "Talamancan montane forests"},
                "NT0175": {"introduced": False, "name": "Venezuelan Andes montane forests"},
                "NT0177": {"introduced": False, "name": "Veracruz montane forests"},
                "NT0181": {"introduced": False, "name": "Yucatn moist forests"},
                "NT0182": {"introduced": False, "name": "Guianan piedmont and lowland moist forests"},
                "NT0201": {"introduced": False, "name": "Apure-Villavicencio dry forests"},
                "NT0202": {"introduced": False, "name": "Atlantic dry forests"},
                "NT0205": {"introduced": False, "name": "Balsas dry forests"},
                "NT0224": {"introduced": False, "name": "Panamanian dry forests"},
                "NT0225": {"introduced": False, "name": "Pata Valley dry forests"},
                "NT0228": {"introduced": False, "name": "Sinaloan dry forests"},
                "NT0229": {"introduced": False, "name": "Sin Valley dry forests"},
                "NT0306": {"introduced": False, "name": "Miskito pine forests"},
                "NT0309": {"introduced": False, "name": "Sierra Madre del Sur pine-oak forests"},
                "NT0702": {"introduced": False, "name": "Beni savanna"},
                "NT0704": {"introduced": False, "name": "Cerrado"},
                "NT0707": {"introduced": False, "name": "Guianan savanna"},
                "NT0801": {"introduced": False, "name": "Espinal"},
                "NT0904": {"introduced": False, "name": "Everglades"},
                "NT0906": {"introduced": False, "name": "Orinoco wetlands"},
                "NT0907": {"introduced": False, "name": "Pantanal"},
                "NT1008": {"introduced": False, "name": "Southern Andean steppe"},
                "NT1308": {"introduced": False, "name": "Guajira-Barranquilla xeric scrub"},
                "NT1316": {"introduced": False, "name": "Tehuacn Valley matorral"},
                "NT1401": {"introduced": False, "name": "Amazon-Orinoco-Southern Caribbean mangroves"},
                "NT1404": {"introduced": False, "name": "Northern Mesoamerican Pacific mangroves"},
                "NT1406": {"introduced": False, "name": "Southern Atlantic mangroves"},
                "NA0303": {"introduced": False, "name": "Sierra Madre Oriental pine-oak forests"},
                "NA0521": {"introduced": False, "name": "Northern transitional alpine forests"},
                "NA0522": {"introduced": False, "name": "Okanagan dry forests"},
                "NA0523": {"introduced": False, "name": "Piney Woods forests"},
                "NA0804": {"introduced": False, "name": "Central forest-grasslands transition"},
                "NA0806": {"introduced": False, "name": "Edwards Plateau savanna"},
                "NA1303": {"introduced": False, "name": "Chihuahuan desert"},
                "NT0136": {"introduced": False, "name": "Magdalena Valley montane forests"},
                "NT0156": {"introduced": False, "name": "Purus varze"},
                "NT0161": {"introduced": False, "name": "Sierra de los Tuxtlas"},
                "NT0176": {"introduced": False, "name": "Veracruz moist forests"},
                "NT0206": {"introduced": False, "name": "Bolivian montane dry forests"},
                "NT0207": {"introduced": False, "name": "Cauca Valley dry forests"},
                "NT0310": {"introduced": False, "name": "Trans-Mexican Volcanic Belt pine-oak forests"},
                "NT0404": {"introduced": False, "name": "Valdivian temperate forests"},
                "NT0708": {"introduced": False, "name": "Humid Chaco"},
                "NT0805": {"introduced": False, "name": "Patagonian steppe"},
                "NA0201": {"introduced": False, "name": "Sonoran-Sinaloan transition subtropical dry forest"},
                "NA0302": {"introduced": False, "name": "Sierra Madre Occidental pine-oak forests"},
                "NA0405": {"introduced": False, "name": "East Central Texas forests"},
                "NA0502": {"introduced": False, "name": "Alberta-British Columbia foothills forests"},
                "NA0503": {"introduced": False, "name": "Arizona Mountains forests"},
                "NA0509": {"introduced": False, "name": "Central British Columbia Mountain forests"},
                "NA0512": {"introduced": False, "name": "Eastern Cascades forests"},
                "NA0514": {"introduced": False, "name": "Fraser Plateau and Basin complex"},
                "NA0515": {"introduced": False, "name": "Great Basin montane forests"},
                "NA0516": {"introduced": False, "name": "Klamath-Siskiyou forests"},
                "NA0518": {"introduced": False, "name": "North Central Rockies forests"},
                "NA0520": {"introduced": False, "name": "Northern Pacific coastal forests"},
                "NA0524": {"introduced": False, "name": "Puget lowland forests"},
                "NA0527": {"introduced": False, "name": "Sierra Nevada forests"},
                "NA0528": {"introduced": False, "name": "South Central Rockies forests"},
                "NA0608": {"introduced": False, "name": "Mid-Continental Canadian forests"},
                "NA0613": {"introduced": False, "name": "Northern Cordillera forests"},
                "NA0801": {"introduced": False, "name": "California Central Valley grasslands"},
                "NA0802": {"introduced": False, "name": "Canadian Aspen forests and parklands"},
                "NA0809": {"introduced": False, "name": "Nebraska Sand Hills mixed grasslands"},
                "NA0810": {"introduced": False, "name": "Northern mixed grasslands"},
                "NA0811": {"introduced": False, "name": "Northern short grasslands"},
                "NA1202": {"introduced": False, "name": "California interior chaparral and woodlands"},
                "NA1203": {"introduced": False, "name": "California montane chaparral and woodlands"},
                "NA1301": {"introduced": False, "name": "Baja California desert"},
                "NA1307": {"introduced": False, "name": "Meseta Central matorral"},
                "NA1309": {"introduced": False, "name": "Snake-Columbia shrub steppe"},
                "NA1313": {"introduced": False, "name": "Wyoming Basin shrub steppe"},
                "NT0101": {"introduced": False, "name": "Araucaria moist forests"},
                "NT0105": {"introduced": False, "name": "Bolivian Yungas"},
                "NT0109": {"introduced": False, "name": "Cauca Valley montane forests"},
                "NT0112": {"introduced": False, "name": "Central American montane forests"},
                "NT0113": {"introduced": False, "name": "Chiapas montane forests"},
                "NT0114": {"introduced": False, "name": "Chimalapas montane forests"},
                "NT0115": {"introduced": False, "name": "Choc-Darin moist forests"},
                "NT0118": {"introduced": False, "name": "Cordillera Oriental montane forests"},
                "NT0119": {"introduced": False, "name": "Costa Rican seasonal moist forests"},
                "NT0125": {"introduced": False, "name": "Guianan moist forests"},
                "NT0128": {"introduced": False, "name": "Iquitos varze"},
                "NT0129": {"introduced": False, "name": "Isthmian-Atlantic moist forests"},
                "NT0133": {"introduced": False, "name": "Juru-Purus moist forests"},
                "NT0138": {"introduced": False, "name": "Maraj varze"},
                "NT0139": {"introduced": False, "name": "Maranho Babau forests"},
                "NT0141": {"introduced": False, "name": "Monte Alegre varze"},
                "NT0142": {"introduced": False, "name": "Napo moist forests"},
                "NT0143": {"introduced": False, "name": "Negro-Branco moist forests"},
                "NT0144": {"introduced": False, "name": "Northeastern Brazil restingas"},
                "NT0146": {"introduced": False, "name": "Oaxacan montane forests"},
                "NT0147": {"introduced": False, "name": "Orinoco Delta swamp forests"},
                "NT0149": {"introduced": False, "name": "Guianan freshwater swamp forests"},
                "NT0150": {"introduced": False, "name": "Alto Paran Atlantic forests"},
                "NT0152": {"introduced": False, "name": "Pernambuco interior forests"},
                "NT0153": {"introduced": False, "name": "Peruvian Yungas"},
                "NT0154": {"introduced": False, "name": "Petn-Veracruz moist forests"},
                "NT0158": {"introduced": False, "name": "Rio Negro campinarana"},
                "NT0159": {"introduced": False, "name": "Santa Marta montane forests"},
                "NT0160": {"introduced": False, "name": "Serra do Mar coastal forests"},
                "NT0164": {"introduced": False, "name": "South Florida rocklands"},
                "NT0168": {"introduced": False, "name": "Tapajs-Xingu moist forests"},
                "NT0169": {"introduced": False, "name": "Pantepui"},
                "NT0173": {"introduced": False, "name": "Uatuma-Trombetas moist forests"},
                "NT0174": {"introduced": False, "name": "Ucayali moist forests"},
                "NT0178": {"introduced": False, "name": "Western Ecuador moist forests"},
                "NT0180": {"introduced": False, "name": "Xingu-Tocantins-Araguaia moist forests"},
                "NT0204": {"introduced": False, "name": "Bajo dry forests"},
                "NT0209": {"introduced": False, "name": "Central American dry forests"},
                "NT0210": {"introduced": False, "name": "Dry Chaco"},
                "NT0211": {"introduced": False, "name": "Chiapas Depression dry forests"},
                "NT0212": {"introduced": False, "name": "Chiquitano dry forests"},
                "NT0214": {"introduced": False, "name": "Ecuadorian dry forests"},
                "NT0217": {"introduced": False, "name": "Jalisco dry forests"},
                "NT0221": {"introduced": False, "name": "Magdalena Valley dry forests"},
                "NT0227": {"introduced": False, "name": "Sierra de la Laguna dry forests"},
                "NT0230": {"introduced": False, "name": "Southern Pacific dry forests"},
                "NT0232": {"introduced": False, "name": "Tumbes-Piura dry forests"},
                "NT0233": {"introduced": False, "name": "Veracruz dry forests"},
                "NT0235": {"introduced": False, "name": "Yucatn dry forests"},
                "NT0302": {"introduced": False, "name": "Belizian pine forests"},
                "NT0303": {"introduced": False, "name": "Central American pine-oak forests"},
                "NT0308": {"introduced": False, "name": "Sierra Madre de Oaxaca pine-oak forests"},
                "NT0703": {"introduced": False, "name": "Campos Rupestres montane savanna"},
                "NT0709": {"introduced": False, "name": "Llanos"},
                "NT0710": {"introduced": False, "name": "Uruguayan savanna"},
                "NT0802": {"introduced": False, "name": "Low Monte"},
                "NT0905": {"introduced": False, "name": "Guayaquil flooded grasslands"},
                "NT0908": {"introduced": False, "name": "Paran flooded savanna"},
                "NT1001": {"introduced": False, "name": "Central Andean dry puna"},
                "NT1002": {"introduced": False, "name": "Central Andean puna"},
                "NT1003": {"introduced": False, "name": "Central Andean wet puna"},
                "NT1005": {"introduced": False, "name": "Cordillera de Merida pramo"},
                "NT1007": {"introduced": False, "name": "Santa Marta pramo"},
                "NT1010": {"introduced": False, "name": "High Monte"},
                "NT1201": {"introduced": False, "name": "Chilean matorral"},
                "NT1303": {"introduced": False, "name": "Atacama desert"},
                "NT1304": {"introduced": False, "name": "Caatinga"},
                "NT1312": {"introduced": False, "name": "Motagua Valley thornscrub"},
                "NT1314": {"introduced": False, "name": "San Lucan xeric scrub"},
                "NT1315": {"introduced": False, "name": "Sechura desert"},
                "NT1403": {"introduced": False, "name": "Mesoamerican Gulf-Caribbean mangroves"},
                "NT1405": {"introduced": False, "name": "South American Pacific mangroves"},
                "NT1407": {"introduced": False, "name": "Southern Mesoamerican Pacific mangroves"},
                "NA0510": {"introduced": False, "name": "Central Pacific coastal forests"},
                "NA0815": {"introduced": False, "name": "Western short grasslands"},
                "NA1302": {"introduced": False, "name": "Central Mexican matorral"},
                "NA1310": {"introduced": False, "name": "Sonoran desert"},
                "NA1312": {"introduced": False, "name": "Tamaulipan mezquital"},
                "NT0126": {"introduced": False, "name": "Gurupa varze"},
                "NT0170": {"introduced": False, "name": "Tocantins/Pindare moist forests"},
                "NT0222": {"introduced": False, "name": "Maracaibo dry forests"},
                "NT0402": {"introduced": False, "name": "Magellanic subpolar forests"},
                "NA0701": {"introduced": False, "name": "Western Gulf coastal grasslands"},
                "NA1117": {"introduced": False, "name": "Pacific Coastal Mountain icefields and tundra"},
                "NT0145": {"introduced": False, "name": "Northwestern Andean montane forests"},
                "NT1006": {"introduced": False, "name": "Northern Andean pramo"},
                "NA0501": {"introduced": False, "name": "Alberta Mountain forests"},
                "NA0530": {"introduced": False, "name": "Wasatch and Uinta montane forests"},
                "NT0307": {"introduced": False, "name": "Sierra de la Laguna pine-oak forests"},
                "NT0909": {"introduced": False, "name": "Southern Cone Mesopotamian savanna"},
            }
        }
    def getprofile(self, query, url, content):
        return {    
            "query": {
                "search": query.get('sciname'),
                "source": "http://mappinglife.org/path/to/data/for/puma_concolor",
                "type": "ecoregions"
                },
            
            "types": {
                "ecoregions": {
                    "names": [query.get('sciname')],
                    "sources": ["WWF"],
                    "layers": [0]
                    }      
                },
            
            "sources": {
                "ecoregions": {
                    "names": [query.get('sciname')],
                    "types": ["ecoregions"],
                    "layers": [0]
                    }, 
                },
            
            "names": {
                query.get('sciname'): {
                    "sources": ["WWF"],
                    "layers": [0],
                    "types": ["ecoregions"]
                    },
                },
            
            "layers": {
                0 : {"name" : query.get('sciname'),
                     "name2" : "WWF Ecoregions", 
                     "source": "WWF",
                     "type": "ecoregions",
                     "count": content["regions"]
                    } 
                }
            }

"""
# class AbstractLayerService(object):
#     '''An abstract base class for the Layer service.'''

#     def is_id_valid(self, id):
#         '''Returns true if the id is valid, otherwise returns false.'''
#         raise NotImplementedError()

# class LayerService(AbstractLayerService):

#     def is_id_valid(self, id):
#         # Checks input for null or empty string:
#         if id is None:
#             return False
#         if len(id.strip()) == 0:
#             return False

#         # Checks if the id can be encoded into a Key:
#         key = None
#         try:
#             key = db.Key(id)
#             if key is None:
#                 return False
#         except BadKeyError:
#             return False

#         # Checks for a Species kind with an entity in the datastore:
#         if key.kind() != 'Species':
#             return False
#         if db.get(key) is None:
#             return False

#         # Passed all checks so id is valid:
#         return True
"""

class TileService(object):
    """A base class for the Tile service."""
    
    def __init__(self,query):
        self.query = query
        self.metadata = None
        self.png = None
        self.url = None
        self.result = None
        self.status = False
        self.rpc = urlfetch.create_rpc()
        self.cachetime = int(41943040 / (2**int(self.query['z'])))
        self.backend = "http://96.126.97.48/layers"
        #self.backend = "http://127.0.0.1:5003/layers"
        self.queue = self.query['queue']
        
    """
    def colortile(self):
        if self.query['r'] is not None:
            self.png = colorPng(self.png, 
                                int(self.query['r']),
                                int(self.query['g']),
                                int(self.query['b']),
                                isObj=True)
        return True
    """
    def tileurl(self):
        if self.url is not None:
            return self.url
        else:
            tileurl = self.backend + "/api/tile/{type}?source={source}&id={id}&r={r}&g={g}&b={b}&x={x}&y={y}&z={z}"
            tileurl = tileurl.replace('{r}', str(self.query['r']))
            tileurl = tileurl.replace('{g}', str(self.query['g']))
            tileurl = tileurl.replace('{b}', str(self.query['b']))
            tileurl = tileurl.replace('{z}', str(self.query['z']))
            tileurl = tileurl.replace('{x}', str(self.query['x']))
            tileurl = tileurl.replace('{y}', str(self.query['y']))
            tileurl = tileurl.replace('{type}', self.query['type'])
            tileurl = tileurl.replace('{source}', self.query['source'])
            tileurl = tileurl.replace('{id}', self.query['id'])
            self.url = tileurl
            return tileurl
        
    def fetchurl(self):
        """Returns a tile from the remote server if needed"""
        if self.result is None:
            try:
                self.rpc.wait()
                self.result = self.rpc.get_result() # This call blocks.
            except:
                return 300
        if self.result.status_code == 204: #means that the tileing job ran, but no data existed in the tile
            return 204
        elif self.result.status_code == 200:
            self.png = self.result.content
            return True
        else:
            return False
        
    def fetchds(self):
        """Returns a tile based on its key if it is available in the datastore"""
        #tile = Tile.get_by_key_name(self.rawkey)
        tile = None
        if tile is not None:
            self.png = tile
            return True
        else:
            return False

    def fetchmc(self, k):
        """Returns a tile based on its key if it is available in memcache"""
        mc = memcache.get(k)
        if mc in [404, 204]:
            return mc
        elif mc is not None:
            self.png = mc
            return True
        else:
            return False
            
    def setmc(self, k, ct=None, status=None):
        if ct is None:
            ct = self.cachetime
        if status is None:
            memcache.set(k, status, ct)
        else:
            memcache.set(k, self.png, ct)
    
    def precache(self):
        ctdown = 0
        x = self.query['x']
        y = self.query['y']
        z = int(self.query['z'])+1
        r = self.query['r'] 
        g = self.query['g'] 
        b = self.query['b']
        if int(x) == 0: 
            x1 = [0,1]
        else:
            x1 = [2*int(x)-1,2*int(x)]
        if int(y) == 0: 
            y1 = [0,1]
        else:
            y1 = [2*int(y)-1,2*int(y)]
        for x0 in x1:
            for y0 in y1:
                key_name = self.query['type'] + "/" + self.query['source'] + "/" + self.query['id']
                url = ''.join(['/data/tile?' ,
                              'key_name=' , key_name ,
                              '&z=' , str(z) ,
                              '&x=' , str(x0) ,
                              '&y=' , str(y0) ,
                              '&r=' , str(r) ,
                              '&g=' , str(g) ,
                              '&b=' , str(b) ,
                              '&queue=False'])
                task = taskqueue.Task(
                            #name="%s-%s-%s-%s-%s-%s-%s-%s" % (datetime.datetime.now().strftime("%Y-%m-%d-%I-%M%p"),
                            name="%s-%s-%s-%s-%s-%s-%s-%s" % (datetime.datetime.now().strftime("%Y-%m-%d"),
                            key_name.replace('/','-'),x0,y0,z,r,g,b),
                            countdown=ctdown, 
                            url = url, 
                            method='GET')
                try:
                    task.add(queue_name='tile-processing-queue')
                except:
                    pass
                ctdown += 2
    def gettile(self):
        """gets a tile based on query parameters"""
        if self.png is not None:
            return
        else:
            """start a url call"""
            self.url = self.tileurl() 
            urlfetch.make_fetch_call(self.rpc, self.url)
            
            mcstatus = self.fetchmc(self.url)
            if mcstatus in [404, 204]:
                self.status = mcstatus
                return
                
            """first check to see if the colored tile is in memcache"""
            """
            if self.query['r'] is not None:
                if self.fetchmc(self.colorkey) is True: 
                    self.setmc(self.colorkey, ct=int(self.cachetime/100))
                    self.status = 200
                    return
            """
            if mcstatus is True: 
                self.status = 200
                if self.queue:
                    self.precache()
                self.setmc(self.url)
                return
            elif self.fetchds() is True:
                self.setmc(self.url)
                self.status = 200
            elif self.fetchurl() == 300:
                self.status = 300
            elif self.fetchurl() == 204:
                self.status = 204 #tiling ran, no data existed in the tile
                self.setmc(self.url, status = 204)
            elif self.fetchurl() is True:
                self.setmc(self.url)
                if self.queue:
                    self.precache()
                self.status = 200
            else: 
                self.setmc(self.url, status = 404)
                self.status = 404
            return self.status

    
