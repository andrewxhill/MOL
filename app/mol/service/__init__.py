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
from google.appengine.api import apiproxy_stub, apiproxy_stub_map, urlfetch
from google.appengine.api.datastore_file_stub import DatastoreFileStub
from google.appengine.ext import db
import logging
from math import ceil
from mol.db import MasterSearchIndex, Tile, TileUpdate, TileSetIndex, MultiPolygon, MultiPolygonIndex, OccurrenceSetIndex, OccurrenceSet
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

def colorPng(img, r, g, b, isObj=False):
    val = None
    logging.error(img)
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
            if ar[row][ct-1]==255:
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
    def __init__(self):
        self.cachetime = 6000
        self.query = {}
        self.types = {}
        self.sources = {}
        self.layers = {}
        self.names = {}
        self.gbifnames = None
        self.keys = None
        self.rpc = None
        self.api_results = None
        self.cachetime = 6000
        self.gbifmemkey = None
        self.gbifquery = True #tells service whether or not to include GBIF results
        
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
                
    def gbifnamesearch(self, query):
        if self.gbifquery:
            self.gbifmemkey = "GBIF/namesearch/%s/%s/%s" % (query.get('term'),query.get('limit', 10),query.get('start', 0))
            self.gbifnames = memcache.get(self.gbifmemkey)  
            if self.gbifnames is None:
                params = urllib.urlencode({
                        'maxResults': query.get('limit', 10),
                        'startIndex': query.get('offset', 0),
                        'query': query.get('term'),
                        'returnType': 'nameId'})
                url = 'http://data.gbif.org/species/nameSearch?%s' % params
                self.rpc = urlfetch.create_rpc()
                urlfetch.make_fetch_call(self.rpc, url)
            
    def _gbifresults(self):
        if self.gbifquery:
            if self.gbifnames is None:
                result = self.rpc.get_result()
                self.gbifnames = []
                ct = 0
                for i in result.content.split('\n'):
                    i = i.strip().split('\t')
                    if len(i)>1:
                        self.gbifnames.append({'name': i[1].strip(), 'subname': 'GBIF Points', 
                                               'category': 'points', 'source': 'GBIF', 'info': None,
                                               'key_name': "points/gbif/%s" % i[0].strip()})
                        ct+=1
                memcache.set(self.gbifmemkey, self.gbifnames, 10*self.cachetime)
            return self.gbifnames
        else:
            return []
        
    def search(self,query,gbifquery=True):
        self.gbifquery = gbifquery
        self.gbifnamesearch(query)
        memkey = "MasterTermSearch/%s/%s/%s" % (query['term'],query['limit'],query['offset'])
        self.keys = memcache.get(memkey)
        self.query = query
        if self.keys is None:
            osi = MasterSearchIndex.all(keys_only=True)
            osi.filter("term =",str(query['term']).lower()).order("-rank")
            res = osi.fetch(limit=query["limit"],offset=query["offset"])
            self.keys = [i.parent() for i in res]
            memcache.set(memkey, self.keys, self.cachetime)
            
    def api_format(self):
        if self.api_results is None:
            ct = 0
            gbifnames = self._gbifresults()
            for r in self.keys:
                r = db.get(r)
                self._addresult(r.category, r.source, r.name, r.subname, r.info, r.key().name(), ct)
            
                ctg = ct%8
                ct+=1
                if (ctg==0 or ct==3) and len(gbifnames)>0:
                    cur = gbifnames.pop(0)
                    self._addresult(cur["category"], 
                                    cur["source"], 
                                    cur["name"], 
                                    cur["subname"], 
                                    cur["info"], 
                                    cur["key_name"], 
                                    ct)
                    ct+=1
                    
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
        return self.api_results
        
        
        

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

class GbifLayerProvider(LayerProvider):
    
    def __init__(self):
        types = [LayerType.POINTS]
        sources = [LayerSource.GBIF]
        super(GbifLayerProvider, self).__init__(types, sources)   
        self.cachetime = 60000   
    
    def geturl(self, query):
        params = urllib.urlencode({
                'format': query.get('format', 'darwin'),
                'coordinateStatus': True,
                'maxResults': query.get('limit', 20),
                'startIndex': query.get('start', 0),
                'scientificname': query.get('sciname')})
        return 'http://data.gbif.org/ws/rest/occurrence/list?%s' % params

    def getdata(self, query):
        rpc = urlfetch.create_rpc()
        url = self.geturl(query)
        urlfetch.make_fetch_call(rpc, url)

        try:
            result = rpc.get_result() 
            if result.status_code == 200:
                return self.xmltojson(result.content, url)
        except (urlfetch.DownloadError), e:
            logging.error('GBIF request: %s (%s)' % (rpc, str(e)))
            #self.error(404) 
            return None
            
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

        return {"source": "GBIF", "sourceUrl": url, "accessDate": str(datetime.datetime.now()), "totalPublishers": pct, "totalResources": rct, "totalRecords": oct, "records": out}
        
    def getprofile(self, query, url, content):
        return {    
            "query": {
                "search": query.get('sciname'),
                "offset": query.get('start', 0),
                "limit": query.get('limit', 200),
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
        self.key = "%s/%s/%s/%s/%s/%s" % (
                        self.query['type'],
                        self.query['source'],
                        self.query['id'],
                        self.query['z'],
                        self.query['x'],
                        self.query['y'] )
        self.metadata = None
        self.png = None
        self.url = None
        self.result = None
        self.status = False
        self.rpc = urlfetch.create_rpc()
        self.cachetime = 6000
        
    def colortile(self):
        """Colors a tile based on R,G,B values"""
        if self.query['r'] is not None:
            """color img here"""
            self.setmc(self.key)
            self.png = colorPng(self.png, 
                                int(self.query['r']),
                                int(self.query['g']),
                                int(self.query['b']),
                                isObj=True)
            self.key = self.key + "/%s/%s/%s" % (self.query['r'],self.query['g'],self.query['b'])
        
        return True
        
    def tileurl(self):
        if self.url is not None:
            return self.url
        else:
            tileurl = "http://mol.colorado.edu/layers/api/tile/{type}?source={source}&id={id}&x={x}&y={y}&z={z}"
            tileurl = tileurl.replace('{z}', str(self.query['z']))
            tileurl = tileurl.replace('{x}', str(self.query['x']))
            tileurl = tileurl.replace('{y}', str(self.query['y']))
            tileurl = tileurl.replace('{type}', self.query['type'])
            tileurl = tileurl.replace('{source}', self.query['source'])
            tileurl = tileurl.replace('{id}', self.query['id'])
            self.url = tileurl
            logging.error(tileurl)
            return tileurl
        
    def fetchurl(self):
        """Returns a tile from the remote server if needed"""
        if self.result is None:
            self.result = self.rpc.get_result() # This call blocks.
            
        if self.result.status_code == 204: #means that the tileing job ran, but no data existed in the tile
            return 204
        elif self.result.status_code == 200:
            self.png = self.result.content
            return True
        else:
            return False
        
    def fetchds(self):
        """Returns a tile based on its key if it is available in the datastore"""
        tile = Tile.get_by_key_name(self.key)
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
            
    def setmc(self, k):
        memcache.set(k, self.png, self.cachetime)
    
    
    def gettile(self):
        """gets a tile based on query parameters"""
        if self.png is not None:
            return
        else:
            """start a url call"""
            self.url = self.tileurl() 
            urlfetch.make_fetch_call(self.rpc, self.url)
            
            mcstatus = self.fetchmc(self.key)
            if mcstatus in [404, 204]:
                self.status = mcstatus
                return
                
            """first check to see if the colored tile is in memcache"""
            if self.query['r'] is not None:
                k = self.key + "/%s/%s/%s" % (self.query['r'],self.query['g'],self.query['b'])
                if self.fetchmc(k) is True: 
                    self.status = 200
                    return
            
            if mcstatus is True: 
                logging.info('memcache')
                self.colortile()
                self.setmc(self.key)
                self.status = 200
            elif self.fetchds() is True:
                self.colortile()
                self.setmc(self.key)
                self.status = 200
            elif self.fetchurl() == 204:
                self.status = 204 #tiling ran, no data existed in the tile
                memcache.set(self.key, 204, self.cachetime)
            elif self.fetchurl() is True:
                self.colortile()
                self.setmc(self.key)
                self.status = 200
            else: 
                memcache.set(self.key, 404, self.cachetime)
                self.status = 404
            return self.status

    
