from google.appengine.ext import db
import cgi, logging, png, copy, math
from django.utils import simplejson

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api.labs import taskqueue
from google.appengine.api import memcache
from google.appengine.ext.webapp import template
from google.appengine.api import images
from google.appengine.api import quota

import os, string, Cookie, sha, time, random, cgi
import urllib, datetime, cStringIO, pickle,random
import wsgiref.handlers
import cStringIO, png

from COL import *
from Tiles import *

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
  def fromKey(self,k):
    results = []
    start = time.time()
    key = db.Key.from_path('Species',k.lower())
    ent = Species.get(key)
    ele = k.split("/")
    e = {
         "rank": str(ele[-2]),
         "name": str(ele[-1]).replace("_"," "),
         "classification": simplejson.loads(ent.classification),
         "authority": simplejson.loads(ent.authority),
         "names": simplejson.loads(ent.names) #.replace('\\','')
        }
    results.append(e)
    t = int(1000*(time.time() - start))/1000.0
    out = {"time":t,"items":results}
    return out
  def fromQuery(self,r,s,of,n):
    start = time.time()
    results = []
    orderOn = r if r is not None else "genus"
    memk = "%s/%s/%s/%s" % (r,s,of,n)
    d = memcache.get(memk)
    if d is None:
        if r is None:
            #q = SpeciesIndex.gql("WHERE names = :1 ORDER BY %s" % orderOn, s.lower())
            q = SpeciesIndex.all(keys_only=True).filter("names =",s.lower()).order(orderOn)
        else:
            q = SpeciesIndex.all(keys_only=True).filter("%s =" % rank,s.lower()).order(orderOn) 
        d = q.fetch(limit=n,offset=of)
    memcache.set(memk,d,3000)
    ct = 0
    for key in d:
        ct+=1
        #ent = Species.get(key.parent())
        ent = db.get(key.parent())
        logging.error(ent.classification)
        p= key.id_or_name().split('/')
        e = {
             "rank": str(p[-2]),
             "name": str(p[-1]).replace("_"," "),
             "classification": simplejson.loads(ent.classification),
             "authority": ent.authority,
             "names": simplejson.loads(ent.names) #.('\\','')
            }
        results.append(e)
    t = int(1000*(time.time() - start))/1000.0
    out = {"time":t,"items":results,"offset":of,"limit":n}
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
        out = self.fromQuery(r,s,of,n)
    else:
        out = self.methods()
            
    #self.response.out.write(simplejson.dumps(out, indent=4))
    self.response.out.write(simplejson.dumps(out).replace("\\/","/"))
    if cb is not None:
        self.response.out.write(")")
        
    
    
bEncode = {
    0 : 'A' , 16 : 'Q' , 32 : 'g' , 48 : 'w' ,
    1 : 'B' , 17 : 'R' , 33 : 'h' , 49 : 'x' ,
    2 : 'C' , 18 : 'S' , 34 : 'i' , 50 : 'y' ,
    3 : 'D' , 19 : 'T' , 35 : 'j' , 51 : 'z' ,
    4 : 'E' , 20 : 'U' , 36 : 'k' , 52 : '0' ,
    5 : 'F' , 21 : 'V' , 37 : 'l' , 53 : '1' ,
    6 : 'G' , 22 : 'W' , 38 : 'm' , 54 : '2' ,
    7 : 'H' , 23 : 'X' , 39 : 'n' , 55 : '3' ,
    8 : 'I' , 24 : 'Y' , 40 : 'o' , 56 : '4' ,
    9 : 'J' , 25 : 'Z' , 41 : 'p' , 57 : '5' ,
    10 : 'K' , 26 : 'a' , 42 : 'q' , 58 : '6' ,
    11 : 'L' , 27 : 'b' , 43 : 'r' , 59 : '7' ,
    12 : 'M' , 28 : 'c' , 44 : 's' , 60 : '8' ,
    13 : 'N' , 29 : 'd' , 45 : 't' , 61 : '9' ,
    14 : 'O' , 30 : 'e' , 46 : 'u' , 62 : '+' ,
    15 : 'P' , 31 : 'f' , 47 : 'v' , 63 : '/' }
    
bDecode = {
    'A' : 0 , 'Q' : 16 , 'g' : 32 , 'w' : 48 ,
    'B' : 1 , 'R' : 17 , 'h' : 33 , 'x' : 49 ,
    'C' : 2 , 'S' : 18 , 'i' : 34 , 'y' : 50 ,
    'D' : 3 , 'T' : 19 , 'j' : 35 , 'z' : 51 ,
    'E' : 4 , 'U' : 20 , 'k' : 36 , '0' : 52 ,
    'F' : 5 , 'V' : 21 , 'l' : 37 , '1' : 53 ,
    'G' : 6 , 'W' : 22 , 'm' : 38 , '2' : 54 ,
    'H' : 7 , 'X' : 23 , 'n' : 39 , '3' : 55 ,
    'I' : 8 , 'Y' : 24 , 'o' : 40 , '4' : 56 ,
    'J' : 9 , 'Z' : 25 , 'p' : 41 , '5' : 57 ,
    'K' : 10 , 'a' : 26 , 'q' : 42 , '6' : 58 ,
    'L' : 11 , 'b' : 27 , 'r' : 43 , '7' : 59 ,
    'M' : 12 , 'c' : 28 , 's' : 44 , '8' : 60 ,
    'N' : 13 , 'd' : 29 , 't' : 45 , '9' : 61 ,
    'O' : 14 , 'e' : 30 , 'u' : 46 , '+' : 62 ,
    'P' : 15 , 'f' : 31 , 'v' : 47 , '/' : 63 }

class Tile(webapp.RequestHandler):
  def get(self):
    self.post()
  def post(self):
    """
    k = self.request.params.get('key', None)
    s = self.request.params.get('specid', None)
    key = "%s/%s/%s" % (s,k,'presence-absence')
    key = db.Key.from_path('Tiles',key.lower())
    data = Tiles.get(key).blob
    img = bin(data)[2:]
    self.response.out.write(img)
    """
    
    chk = lambda v, l: [v[i*l:(i+1)*l] for i in range(int(math.ceil(len(v)/float(l))))]
    #fix = lambda v: int(c) for c in v
    t = TmpTiles.all().fetch(1)[0]
    b = ''
    for c in t.band:
        b += str(bin(bDecode[c])[2:])
    s = chk(b,256)
    s = map(lambda x: map(int, x), s)
    """
    f = cStringIO.StringIO()
    palette=[(0xff,0xff,0xff,0x00),(0x00,0x00,0x00,0xff)]
    p = png.Writer(PIXELS,PIXELS, palette=palette, bitdepth=1)
    p.write(f,b)
    """
    #self.response.out.write(f.getvalue())
    #self.response.out.write(PIXELS)
    
    f = cStringIO.StringIO()
    w = png.Writer(len(s[0]), len(s), greyscale=True, bitdepth=1)
    w.write(f, s)

    # binary PNG data
    self.response.headers['Content-Type'] = 'image/png'
    self.response.out.write(f.getvalue())
    
      
application = webapp.WSGIApplication(
         [('/api/taxonomy', Taxonomy),      
         ('/api/tile', Tile)],      
         debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
