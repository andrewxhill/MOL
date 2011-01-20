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
from google.appengine.ext import webapp, db
from google.appengine.ext.webapp.util import run_wsgi_app
from mol.db import Species, SpeciesIndex, TileSetIndex
from mol.services import TileService, LayerService
import logging
import time, datetime
import os
import pickle
from google.appengine.api.datastore_errors import BadKeyError

HTTP_STATUS_CODE_NOT_FOUND = 404

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
        results.append(e)
    t = int(1000 * (time.time() - start)) / 1000.0
    out = {"time":t, "items":results, "offset":of, "limit":n}
    return out

  def get(self):
    self.post()

  def post(self):
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
            self.response.out.write(t.band)
        
class UpdateLayerMetadata(webapp.RequestHandler):
    """RequestHandler for remote server to update layer metadata."""  
    def __init__(self):
        super(UpdateLayerMetadata, self).__init__()
        self.authIPs = ['128.138.167.165', '127.0.0.1'] #allow localhost testing and the MOL server only
    def post(self):
        data = {}
        if os.environ['REMOTE_ADDR'] in self.authIPs:
            id = self.request.params.get('id')
            data['zoom'] = self.request.params.get('zoom')
            data['proj'] = self.request.params.get('proj')
            date = self.request.params.get('date')
            data['date'] = datetime.datetime.strptime(date.split('.')[0], "%Y-%m-%d %H:%M:%S")
            data['maxLat'] = self.request.params.get('maxLat')
            data['minLat'] = self.request.params.get('minLat')
            data['maxLon'] = self.request.params.get('maxLon')
            data['minLon'] = self.request.params.get('minLon')
            data['remoteLocation'] = self.request.params.get('remoteLocation')
            if id is not None:
                """this part does not work, i didn't have available Species entities to test with"""
                key = db.Key(id)
                md = TileSetIndex.get_by_key_name(key.name())
                if md is None:
                    md = TileSetIndex(name=key.name())
                    #md = TileSetIndex(name=id)
                """store or overwrite the data in the model"""
                try:
                    if md.dateLastModified is not None and md.dateLastModified > data['date']:
                        """if the metadata shipped is older than the metadata on GAE then don't store"""
                        self.response.out.write('{response: {status: "failed", id: %s, error: "newer layer exists"}}' % id) 
                    else:
                        md.zoom = int(data['zoom'])
                        md.proj = data['proj']
                        md.maxLat = float(data['maxLat'])
                        md.minLat = float(data['minLat'])
                        md.maxLon = float(data['maxLon'])
                        md.minLon = float(data['minLon'])
                        md.remoteLocation = data['remoteLocation']
                        md.dateLastModified = data['date']
                        md.put()
                        """cache the new data"""
                        mcData = pickle.dumps(data, pickle.HIGHEST_PROTOCOL)
                        memcache.set("meta-%s" % id, mcData, 2592000) #cache the layer data for 30 days
                        
                        self.response.out.write('{response: {status: "updated", id: %s}}' % id) 
                except Exception, e:
                    self.response.out.write('{response: {status: "failed", id: %s, error: "%s"}}' % (id, e))
                    
                if key_name:
                    key = db.Key.from_path('TileSetIndex', key_name)
                    md = TileSetIndex.get(key)
                    if md is None:
                        md = TileSetIndex(key=key)
                    """store or overwrite the data in the model"""
                    try:
                        if md.dateLastModified is not None and md.dateLastModified > data['date']:
                            """if the metadata shipped is older than the metadata on GAE then don't store"""
                            self.response.out.write('{response: {status: "failed", id: %s, error: "newer layer exists"}}' % id) 
                        else:
                            md.zoom = int(data['zoom'])
                            md.proj = data['proj']
                            md.maxLat = float(data['maxLat'])
                            md.minLat = float(data['minLat'])
                            md.maxLon = float(data['maxLon'])
                            md.minLon = float(data['minLon'])
                            md.remoteLocation = data['remoteLocation']
                            md.dateLastModified = data['date']
                            md.put()
                            """cache the new data"""
                            mcData = pickle.dumps(data, pickle.HIGHEST_PROTOCOL)
                            memcache.set("meta-%s" % id, mcData, 2592000) #cache the layer data for 30 days
                            
                            self.response.out.write('{response: {status: "updated", id: %s}}' % id) 
                    except Exception, e:
                        self.response.out.write('{response: {status: "failed", id: %s, error: "%s"}}' % (id, e)) 
                    
            
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
        
application = webapp.WSGIApplication(
         [('/api/taxonomy', Taxonomy),
          ('/api/validid', ValidLayerID),
          ('/api/tile/[\d]+/[\d]+/[\w]+.png', TilePngHandler),
          ('/api/layer/update', UpdateLayerMetadata)],
         debug=True)
         
def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
