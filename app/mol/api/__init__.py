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
from google.appengine.api import memcache
from google.appengine.api.datastore_errors import BadKeyError, BadArgumentError
from google.appengine.ext import webapp, db
from google.appengine.ext.db import KindError
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from gviz import gviz_api
from mol.db import Species, SpeciesIndex, TileSetIndex
from mol.services import TileService, LayerService
import logging
import os
import pickle
import time
import datetime
import wsgiref.util

HTTP_STATUS_CODE_NOT_FOUND = 404
HTTP_STATUS_CODE_FORBIDDEN = 403
HTTP_STATUS_CODE_BAD_REQUEST = 400

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
            e = {
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
        gql = params.get('gql')
        rank = params.get('rank', None)
        key = params.get('key', None)

        # Gets the data for the request:
        if key:
            out = self.fromKey(key)
        elif gql is not None:
            out = self.fromQuery(rank, gql, offset, limit)
        data = out.get('items')
        #data = simplejson.loads("""[{"authority": "COL", "classification": {"kingdom": "animalia", "superfamily": null, "family": "pomacentridae", "author": "Gill, 1862", "class": "actinopterygii", "infraspecies": null, "phylum": "chordata", "genus": "abudefduf", "order": "perciformes", "species": "concolor"}, "name": "abudefduf concolor", "rank": "species", "names": [{"source": "COL", "type": "common name", "name": "Tono", "language": "Spanish", "author": null}, {"source": "COL", "type": "common name", "name": "Petaca rebozada", "language": "Spanish", "author": null}, {"source": "COL", "type": "common name", "name": "Petaca", "language": "Spanish", "author": null}, {"source": "COL", "type": "common name", "name": "M\u00f8rk sergentfisk", "language": "Danish", "author": null}, {"source": "COL", "type": "common name", "name": "Night sergeant", "language": "English", "author": null}, {"source": "COL", "type": "common name", "name": "Dusky seargent", "language": "English", "author": null}, {"source": "COL", "type": "common name", "name": "Chauffet de nuit", "language": "French", "author": null}, {"source": "COL", "type": "common name", "name": "Ayangue pardo", "language": "Spanish", "author": null}, {"source": "COL", "type": "common name", "name": "&#38620;&#33394;&#35910;&#23064;&#39770;", "language": "Mandarin Chinese", "author": null}, {"source": "COL", "type": "common name", "name": "&#26434;&#33394;&#35910;&#23064;&#40060;", "language": "Mandarin Chinese", "author": null}, {"source": "COL", "type": "accepted name", "name": "Abudefduf concolor", "language": "latin", "author": "Gill, 1862"}, {"source": "COL", "type": "scientific name", "name": "Pomacentrus robustus", "language": "latin", "author": "G\u00fcnther, 1862"}, {"source": "COL", "type": "scientific name", "name": "Euschistodus concolor", "language": "latin", "author": "Gill, 1862"}]}]""", encoding='utf-8')

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

            #for name in rec['classification'].keys():
            #    row[name] = rec['classification'][name]

            names_csv = ''
            for name in rec['names']:
                names_csv += name['name'].capitalize() + ','
            row['Synonyms CSV'] = names_csv[:-1]
            rows.append(row)

        # Builds DataTable for Google Visualization API:
        description = {'Accepted Name': ('string', 'accepted name'),
                       'Author': ('string', 'author'),
                       'Kingdom/Phylum/Class/Order/Family': ('string', 'Kingdom/Pyhlum/Cass/Family'),
                       'Synonyms CSV': ('string', 'synonyms csv')}

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

class ValidLayerID(webapp.RequestHandler):
    """RequestHandler for testing MOL id authenticity."""
    def __init__(self):
        super(ValidLayerID, self).__init__()
        self.layer_service = LayerService()

    def get(self):
        id = self.request.params.get('id')
        if self.layer_service.is_id_valid(id):
            self.response.out.write(id)
        else:
            self.error(404)

class BaseHandler(webapp.RequestHandler):
    '''Base handler for handling common stuff like template rendering.'''
    def render_template(self, file, template_args):
        path = os.path.join(os.path.dirname(__file__), "templates", file)
        self.response.out.write(template.render(path, template_args))


class LayersHandler(BaseHandler):

    AUTHORIZED_IPS = ['128.138.167.165', '127.0.0.1']

    def param(self, name, required=True, type=str):
        val = self.request.get(name, None)
        if required and val is None:
            logging.error('%s is required' % name)
            raise BadArgumentError
        try:
            return type(val)
        except (ValueError), e:
            logging.error('Invalid %s %s: %s' % (name, val, e))
            raise BadArgumentError(e)

    def _update(self, metadata):
        dlm = self.request.params.get('dateCreated', None)
        dlm = datetime.datetime.strptime(dlm.split('.')[0], "%Y-%m-%d %H:%M:%S")
        if metadata.dateLastModified > dlm:
            self.error(409) # Conflict
            return
        enw = db.GeoPt(self.param('maxLat', type=float), self.param('minLon', type=float))
        ese = db.GeoPt(self.param('minLat', type=float), self.param('maxLon', type=float))
        metadata.extentNorthWest = enw
        metadata.extentSouthEast = ese
        metadata.dateLastModified = datetime.datetime.now()
        metadata.remoteLocation = db.Link(self.param('remoteLocation'))
        metadata.zoom = self.param('zoom', type=int)
        metadata.proj = self.param('proj')
        db.put(metadata)
        location = wsgiref.util.request_uri(self.request.environ).split('?')[0]
        self.response.headers['Location'] = location
        self.response.headers['Content-Location'] = location
        self.response.set_status(204) # No Content

    def _create(self, specimen_id):
        enw = db.GeoPt(self.param('maxLat', type=float), self.param('minLon', type=float))
        ese = db.GeoPt(self.param('minLat', type=float), self.param('maxLon', type=float))
        db.put(TileSetIndex(key=db.Key.from_path('TileSetIndex', specimen_id),
                            dateLastModified=datetime.datetime.now(),
                            remoteLocation=db.Link(self.param('remoteLocation')),
                            zoom=self.param('zoom', type=int),
                            proj=self.param('proj'),
                            extentNorthWest=enw,
                            extentSouthEast=ese))
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

    def get(self, specimen_id=None):
        '''Gets a TileSetIndex identified by a MOL specimen id 
        (/layers/specimen_id) or all TileSetIndex entities (/layers).
        '''
        if specimen_id is None or len(specimen_id) is 0:
            # Sends all metadata:
            self.response.headers['Content-Type'] = 'application/json'
            all = [self._getprops(x) for x in TileSetIndex.all()]
            # TODO: This response will get huge so we need a strategy here.
            self.response.out.write(simplejson.dumps(all))
            return
        metadata = TileSetIndex.get_by_key_name(specimen_id)
        if metadata:
            self.response.headers['Content-Type'] = 'application/json'
            self.response.out.write(simplejson.dumps(self._getprops(metadata)))
        else:
            self.error(404) # Not found

    def put(self, specimen_id):
        '''Creates a TileSetIndex entity or updates an existing one if the 
        incoming data is newer than what is stored in GAE.'''
        remote_addr = os.environ['REMOTE_ADDR']
        if not remote_addr in LayersHandler.AUTHORIZED_IPS:
            logging.warning('Unauthorized PUT request from %s' % remote_addr)
            self.error(401) # Not authorized
            return
        try:
            metadata = TileSetIndex.get_by_key_name(specimen_id)
            if metadata:
                self._update(metadata)
            else:
                self._create(specimen_id)
        except (BadArgumentError), e:
            logging.error('Bad PUT request %s: %s' % (specimen_id, e))
            self.error(400) # Bad request

application = webapp.WSGIApplication(
         [('/api/taxonomy', Taxonomy),
          ('/api/validid', ValidLayerID),
          ('/api/tile/[\d]+/[\d]+/[\w]+.png', TilePngHandler),
          #('/api/layer/update', UpdateLayerMetadata),
          ('/layers/([\w]*)', LayersHandler),
          ('/layers', LayersHandler), ],
         debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
