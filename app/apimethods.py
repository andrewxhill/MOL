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

bDecode = {'+': '111110', '/': '111111', '1': '110101', '0': '110100', '3': '110111', '2': '110110', '5': '111001', '4': '111000', '7': '111011', '6': '111010', '9': '111101', '8': '111100', 'A': '000000', 'C': '000010', 'B': '000001', 'E': '000100', 'D': '000011', 'G': '000110', 'F': '000101', 'I': '001000', 'H': '000111', 'K': '001010', 'J': '001001', 'M': '001100', 'L': '001011', 'O': '001110', 'N': '001101', 'Q': '010000', 'P': '001111', 'S': '010010', 'R': '010001', 'U': '010100', 'T': '010011', 'W': '010110', 'V': '010101', 'Y': '011000', 'X': '010111', 'Z': '011001', 'a': '011010', 'c': '011100', 'b': '011011', 'e': '011110', 'd': '011101', 'g': '100000', 'f': '011111', 'i': '100010', 'h': '100001', 'k': '100100', 'j': '100011', 'm': '100110', 'l': '100101', 'o': '101000', 'n': '100111', 'q': '101010', 'p': '101001', 's': '101100', 'r': '101011', 'u': '101110', 't': '101101', 'w': '110000', 'v': '101111', 'y': '110010', 'x': '110001', 'z': '110011'}

class Tile(webapp.RequestHandler):
  def post(self):
    self.get()
  def get(self):
      
    """
        out = []
        m = {(0,0):'q', (0,1):'t', (1,0):'r', (1,1):'s'}
        for i in range(17-zoom):
            x, rx = divmod(x, 2)
            y, ry = divmod(y, 2)
            out.insert(0, m[(rx,ry)])
        return 't' + ''.join(out)
        """
    #convert the URL route into the key (removing .png)
    url = self.request.path_info
    assert '/' == url[0]
    path = url[1:]
    if '/' in path:
        (b1,b2, k) = path.split("/", 2)
        k = k.split('.')[0]
    else:
        k = '00/210'
        
    key = "%s/%s" % (k,'presence')
    """
    key = db.Key.from_path('Tiles',key.lower())
    data = Tiles.get(key).blob
    img = bin(data)[2:]
    self.response.out.write(img)
    """
    t = TmpTiles.gql("WHERE keyLiteral = '%s'" % key).fetch(1)[0]
    
    chk = lambda v, l: [v[i*l:(i+1)*l] for i in range(int(math.ceil(len(v)/float(l))))]
    #fix = lambda v: int(c) for c in v
    b = ''
    ct = 0
    for c in t.band:
        b += bDecode[c]
        
    #we should try to combine the follow two steps into a single function
    s = chk(b,256)
    s = map(lambda x: map(int, x), s)

    
    f = cStringIO.StringIO()
    palette=[(0xff,0xff,0xff,0x00),(0x00,0x00,0x00,0xff)]
    w = png.Writer(256,256, palette=palette, bitdepth=1)
    w.write(f, s)

    # binary PNG data
    self.response.headers['Content-Type'] = 'image/png'
    self.response.out.write(f.getvalue())
    
      
application = webapp.WSGIApplication(
         [('/api/taxonomy', Taxonomy),      
         ('/api/tile/[^/]+/[^/]+.png', Tile)],      
         debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
