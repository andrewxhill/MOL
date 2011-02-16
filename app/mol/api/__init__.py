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
from django.utils import simplejson
from google.appengine.api import urlfetch
from google.appengine.api.datastore_errors import BadKeyError, BadArgumentError
from google.appengine.api.memcache import Client
from google.appengine.ext import webapp, db
from google.appengine.ext.db import KindError
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from gviz import gviz_api
from mol.db import Species, SpeciesIndex, TileSetIndex, Tile
import datetime
import logging
import os
import pickle
import time
import wsgiref.util
from mol.services import TileService

memcache = Client()

HTTP_STATUS_CODE_NOT_FOUND = 404
HTTP_STATUS_CODE_FORBIDDEN = 403
HTTP_STATUS_CODE_BAD_REQUEST = 400

class FindID(webapp.RequestHandler):
    def get(self, a, id):
        q = SpeciesIndex.all(keys_only=True).filter("authorityName =", a).filter("authorityIdentifier =", id)
        d = q.fetch(limit=2)
        if len(d) == 2:
            return "multiple matches"
        elif len(d) == 0:
            return 400
        else:
            k = d[0]
            self.response.out.write(str(k.name()))
            

class TileSetMetadata(webapp.RequestHandler):
    def _getprops(self, obj):
        '''Returns a dictionary of entity properties as strings.'''
        dict = {}
        for key in obj.properties().keys():
            if key in ['extentNorthWest', 'extentSouthEast', 'status', 'zoom', 'dateCreated', 'dateLastModified', 'proj', 'type']:
                dict[key] = str(obj.properties()[key].__get__(obj, TileSetIndex))
            """
            elif key in []:
                c = str(obj.properties()[key].__get__(obj, TileSetIndex))
                d = c.split(',')
                dict[key] = {"latitude":float(c[1]),"longitude":float(c[0])}
            """
        dict['mol_species_id'] = str(obj.key().name())
        return dict
    def get(self, class_, rank, species_id=None):
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
        
class Taxonomy(webapp.RequestHandler):

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

    def fromQuery(self, r, s, of, n):
        start = time.time()
        results = []
        orderOn = r if r is not None else "genus"
        memk = "%s/%s/%s/%s" % (r, s, of, n)
        d = memcache.get(memk)
        if d is None:
            if r is None:
                #q = SpeciesIndex.gql("WHERE names = :1 ORDER BY %s" % orderOn, s.lower())
                q = SpeciesIndex.all(keys_only=True).filter("names =", s.lower()).order(orderOn)
            else:
                q = SpeciesIndex.all(keys_only=True).filter("%s =" % rank, s.lower()).order(orderOn)
            d = q.fetch(limit=n, offset=of)
        memcache.set(memk, d, 3000)
        ct = 0
        for key in d:
            ct += 1
            #ent = Species.get(key.parent())
            ent = db.get(key.parent())
            logging.error(ent.classification)
            p = key.id_or_name().split('/')
            e = {"key_name" : key.name(),
                 "rank": str(p[-2]),
                 "name": str(p[-1]).replace("_", " "),
                 "classification": simplejson.loads(ent.classification),
                 "authority": ent.authority,
                 "names": simplejson.loads(ent.names) #.('\\','')
                }
            logging.info('ent.NAMES ' + ent.names)
            logging.info('e.NAMES ' + str(e['names']))
            results.append(e)
        t = int(1000 * (time.time() - start)) / 1000.0
        out = {"time":t, "items":results, "offset":of, "limit":n}
        return out

    def get(self):
        self.post()

    def handle_data_source_request(self):
        tq = self.request.get('tq')
        params = simplejson.loads(tq)
        limit = params.get('limit')
        offset = params.get('offset')
        gql = params.get('gql').strip()
        rank = params.get('rank', None)
        key = params.get('key', None)

        # Gets the data for the request:
        if key:
            out = self.fromKey(key)
        elif gql is not None:
            out = self.fromQuery(rank, gql, offset, limit)
        data = out.get('items')

        # TODO: how to handle 'classification' and 'names' in table format?
        # Right now just flattening classification and ignoring names...
        rows = []
        for rec in data:
            row = {'Accepted Name':rec['name'].capitalize(), 'Author':rec['classification']['author']} #{'authority':rec['authority'], 'name':rec['name'], 'rank':rec['rank']}
            taxonomy = '%s/%s/%s/%s/%s' % (rec['classification']['kingdom'].capitalize(),
                                           rec['classification']['phylum'].capitalize(),
                                           rec['classification']['class'].capitalize(),
                                           rec['classification']['order'].capitalize(),
                                           rec['classification']['family'].capitalize())
            row['Kingdom/Phylum/Class/Order/Family'] = taxonomy
                        
            names_csv = ''
            for name in rec['names']:
                names_csv += name['name'].capitalize() + ','
            row['Synonyms CSV'] = names_csv[:-1]
            
            
            key_name = rec['key_name']
            logging.info('key_name ' + key_name)
            if TileSetIndex.get_by_key_name(key_name) is not None:
                row['Range Map'] = '<a href="/rangemap/%s">map</a>' % key_name
            else:
                row['Range Map'] = ''

            
            rows.append(row)
            
            

        # Builds DataTable for Google Visualization API:
        description = {'Accepted Name': ('string', 'accepted name'),
                       'Author': ('string', 'author'),
                       'Kingdom/Phylum/Class/Order/Family': ('string', 'Kingdom/Pyhlum/Class/Family'),
                       'Synonyms CSV': ('string', 'synonyms csv'),
                       'Range Map': ('string', 'range map')}

        if len(rows) > 0:
            spec = rows[0]
            logging.info(type(spec))
            for key in spec.keys():
                description[key] = ('string', key)
            data_table = gviz_api.DataTable(description)
            data_table.LoadData(rows)
        else:
            data_table = gviz_api.DataTable({'GUID':('string', '')})

        # Sends the DataTable response:
        tqx = self.request.get('tqx')
        self.response.out.write(data_table.ToResponse(tqx=tqx))

    def post(self):

        # Checks for and handles a Google Visualization data source request:
        tqx = self.request.get('tqx', None)
        if tqx is not None:
            logging.info(type(tqx))
            self.handle_data_source_request()
            return

        # Handle a normal API request:
        cb = self.request.params.get('callback', None)
        if cb is not None:
            self.response.out.write("%s(" % cb)
        k = self.request.params.get('key', None)
        s = self.request.params.get('search', None)
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
        self.response.out.write(simplejson.dumps(out).replace("\\/", "/"))
        if cb is not None:
            self.response.out.write(")")

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
        logging.info(path)
        self.response.out.write(template.render(path, template_args))

class RangeMapHandler(BaseHandler):
    '''Handler for rendering range maps based on species key_name.'''
    def get(self, class_, rank, species):
        key_name = os.path.join(class_, rank, species)
        self.render_template('rangemap.html', {})
                
class LayersTileHandler(BaseHandler):

    def get(self, class_, rank, png_name):
        '''Handles a PNG map tile request according to the Google XYZ tile 
        addressing scheme described here:
        
        http://code.google.com/apis/maps/documentation/javascript/v2/overlays.html#Google_Maps_Coordinates
        
        Required query string parameters:
            z - integer zoom level
            y - integer latitude pixel coordinate
            x - integer longitude pixel coordinate
        '''
        species_id, ext = os.path.splitext(png_name)
        species_key_name = os.path.join(class_, rank, species_id)
        logging.info('KEY NAME ' + species_key_name)
        # Returns a 404 if there's no TileSetIndex for the species id since we 
        # need it to calculate bounds and for the remote tile URL:
        metadata = TileSetIndex.get_by_key_name(species_key_name)
        if metadata is None:
            logging.error('No metadata for species: ' + species_key_name)
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

        # Returns a 404 if the request isn't within bounds of the species:
        within_bounds = True; # TODO: Calculate if within bounds.
        if not within_bounds:
            self.error(404) # Not found
            return

        # Builds the tile image URL which is also the memcache key. It's of the
        # form: http://mol.colorado.edu/tiles/species_id/zoom/x/y.png
        tileurl = metadata.remoteLocation
        tileurl = tileurl.replace('zoom', zoom)
        tileurl = tileurl.replace('/x/', '/%s/' % x)
        tileurl = tileurl.replace('y.png', '%s.png' % y)
        
        logging.info('Tile URL ' + tileurl)

        # Starts an async fetch of tile in case we get a memcache/datastore miss: 
        # TODO: Optimization would be to async fetch the 8 surrounding tiles.
        rpc = urlfetch.create_rpc()
        urlfetch.make_fetch_call(rpc, tileurl)

        # Checks memcache for tile and returns it if found:
        memcache_key = "tileurl-%s" % tileurl
        band = memcache.get(memcache_key)
        if band is not None:
            logging.info('Tile memcache hit: ' + memcache_key)
            self.response.headers['Content-Type'] = "image/png"
            self.response.out.write(band)
            return

        # Checks datastore for tile and returns if found:
        tile_key_name = os.path.join(species_key_name, zoom, y, x)
        tile = Tile.get_by_key_name(tile_key_name)
        if tile is not None:
            logging.info('Tile datastore hit: ' + tile_key_name)
            memcache.set(memcache_key, tile.band, 60)
            self.response.headers['Content-Type'] = "image/png"
            self.response.out.write(tile.band)
            return

        # Gets downloaded tile from async rpc request and returns it or a 404: 
        try:
            result = rpc.get_result() # This call blocks.
            if result.status_code == 200:
                logging.info('Tile downloaded: ' + tileurl)
                band = result.content
                memcache.set(memcache_key, band, 60)
                self.response.headers['Content-Type'] = "image/png"
                self.response.out.write(band)
            else:
                raise urlfetch.DownloadError('Bad tile result ' + str(result))
        except (urlfetch.DownloadError), e:
            logging.error('%s - %s' % (tileurl, str(e)))
            logging.info('Status=%s, URL=%s' % (str(result.status_code), result.final_url))
            self.error(404) # Not found

class LayersHandler(BaseHandler):

    AUTHORIZED_IPS = ['128.138.167.165', '127.0.0.1', '71.202.235.132']

    def _update(self, metadata):
            
        dlm = self._param('dateCreated')
        dlm = datetime.datetime.strptime(dlm.split('.')[0], "%Y-%m-%d %H:%M:%S")
        if metadata.dateLastModified > dlm:
            logging.info('TileSetIndex.dlm=%s, metadata.dlm=%s' % (metadata.dateLastModified, dlm))
            self.error(409) # Conflict
            return
            
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


application = webapp.WSGIApplication(
         [('/api/taxonomy', Taxonomy),
          ('/api/findid/([^/]+)/([^/]+)', FindID),
          ('/api/tile/[\d]+/[\d]+/[\w]+.png', TilePngHandler),
          ('/api/tile/metadata/([^/]+)/([^/]+)/([\w]+)', TileSetMetadata),
          ('/layers/([^/]+)/([^/]+)/([\w]+)', LayersHandler),
          ('/rangemap/([^/]+)/([^/]+)/([\w]+)', RangeMapHandler),
          ('/layers/([^/]+)/([^/]+)/([\w]*.png)', LayersTileHandler),
          ('/layers', LayersHandler), ],
         debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
