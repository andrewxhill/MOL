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
from mol.db import Tile, TileUpdate, TileSetIndex
from xml.etree import ElementTree as etree
import datetime
import cStringIO
import os
import png
import re
import urllib
from google.appengine.api.datastore_errors import BadKeyError

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
    
    def geturl(self, query):
        params = urllib.urlencode({
                'format': query.get('format', 'darwin'),
                'coordinatestatus': True,
                'maxresults': query.get('limit', 200),
                'startindex': query.get('start', 0),
                'scientificname': query.get('sciname')})
        return 'http://data.gbif.org/ws/rest/occurrence/list?%s' % params

    def getdata(self, query):
        rpc = urlfetch.create_rpc()
        urlfetch.make_fetch_call(rpc, self.geturl(query))

        try:
            result = rpc.get_result() 
            if result.status_code == 200:
                return result.content
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
            logging.info('element.text:%s, type:%s ' % (element.text, type(element.text)))
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
        rpc = urlfetch.create_rpc()
        urlfetch.make_fetch_call(rpc, self.geturl(query))

        try:
            result = rpc.get_result() 
            if result.status_code == 200:
                return result.content
        except (urlfetch.DownloadError), e:
            logging.error('GBIF request: %s (%s)' % (rpc, str(e)))
            #self.error(404) 
            return None
            
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

    
# class AbstractLayerService(object):
#     """An abstract base class for the Layer service."""

#     def is_id_valid(self, id):
#         """Returns true if the id is valid, otherwise returns false."""
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

class AbstractTileService(object):
    """An abstract base class for the Tile service."""

    def put_tile(self, tile):
        """Puts a Tile in the datastore. Returns a key or None if it wasn't put."""
        raise NotImplementedError()

    def put_tile_update(self, tile):
        """Puts a TileUpdate for a Tile in the datastore. Returns a key or None if
        it wasn't put.
        """
        raise NotImplementedError()

    def tile_from_url(self, url):
        """Returns the Tile associated with a entity URL request url or None if a
        Tile could not be found."""
        raise NotImplementedError()

class TileService(AbstractTileService):

    KEY_NAME_PATTERN = '[\d]+/[\d]+/[\w]+'
    TILE_KIND = 'Tile'
    TILE_UPDATE_KIND = 'TileUpdate'

    @staticmethod
    def _is_tile(tile):
        return tile is not None and isinstance(tile, Tile)

    @staticmethod
    def _zoom_from_key_name(key_name):
        if key_name is None:
            return None
        if key_name.count('/') < 2:
            return None
        zoom = key_name.split('/')[1]
        try:
            int(zoom)
        except ValueError:
            return None
        return zoom

    def put_tile(self, tile, update=True):
        if not TileService._is_tile(tile):
            return None
        key = db.put(tile)
        if update:
            self.put_tile_update(tile)
        return key

    def put_tile_update(self, tile):
        if not TileService._is_tile(tile):
            return None
        if not tile.is_saved() or tile.key().name() is None:
            return None
        key_name = tile.key().name()
        zoom = self._zoom_from_key_name(key_name)
        if zoom is None:
            return None
        tu_key = db.Key.from_path(self.TILE_UPDATE_KIND, key_name)
        tu = TileUpdate(key=tu_key)
        tu.zoom = len(zoom)
        tu_key = db.put(tu)
        return tu_key

    def tile_from_url(self, url):
        if url is None:
            return None
        key = self._key_name(url)
        if key is None:
            return None
        entity = Tile.get(key)
        return entity

    def _key_name(self, string):
        if string is None:
            return None
        try:
            key_name = re.findall(self.KEY_NAME_PATTERN, string)[0]
            key = db.Key.from_path(self.TILE_KIND, key_name)
            return key
        except IndexError:
            return None
