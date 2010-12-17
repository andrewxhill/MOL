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
from mol.db import Species, SpeciesIndex
from mol.services import TileService
import logging
import time

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
            
        if cmp(tmp,'f')==0:
            self.redirect("/static/full.png")
        else:
            self.response.headers['Content-Type'] = "image/png"
            self.response.out.write(t.band)
            
            
application = webapp.WSGIApplication(
         [('/api/taxonomy', Taxonomy),
         ('/api/tile/[\d]+/[\d]+/[\w]+.png', TilePngHandler)], 
         debug=True)
         
def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
