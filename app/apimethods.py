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
    #k = "00/21"
    key = "%s/%s" % (k,'presence')
    key = db.Key.from_path('TmpTiles',key)
    t = TmpTiles.get(key)
    """
    key = db.Key.from_path('Tiles',key.lower())
    data = Tiles.get(key).band
    img = bin(data)[2:]
    self.response.out.write(img)
    """
    #t = TmpTiles.gql("WHERE keyLiteral = '%s'" % key).fetch(1)[0]
    if t:
        chk = lambda v, l: [v[i*l:(i+1)*l] for i in range(int(math.ceil(len(v)/float(l))))]
        #fix = lambda v: int(c) for c in v
        b = ''
        ct = 0
        for c in t.band:
            b += bDecode[c]
            
        #we should try to combine the follow two steps into a single function
        s = chk(b[:-3],256)
        s = map(lambda x: map(int, x), s)

        
        f = cStringIO.StringIO()
        palette=[(0xff,0xff,0xff,0x00),(0x00,0x00,0x00,0xff)]
        w = png.Writer(256,256, palette=palette, bitdepth=1)
        w.write(f, s)

        # binary PNG data
        self.response.headers['Content-Type'] = 'image/png'
        self.response.out.write(f.getvalue())

class InterpolateTile(webapp.RequestHandler):
  def post(self):
    self.get()
  def get(self):
      
    #from now on, assume the key sent was k="01"
    key = self.request.params.get('k', None)
    
    bands = []
    
    #we just want a list with a '0' pixel place holder for every pixel in a 256x256 PNG
    n = "0" * 65536
    n = list(n)
    
    #the way that quadtree logic works, is that every tile of 256x256, is quartered
    #into 4 equal tiles when you zoom into it. The naming is super simple and nice
    #at zoom 0, there is 1 tile, with an id= 0
    #if you then zoom in, there are 4 tiles: 00, 01, 02, 03
    #so given a key of 0, we know that we have to group together all the information
    #from 00,01,02,03 to make the courser tile, hence the loop below
    for qt in [0,1,2,3]: #get all four tiles that make up the greater tile
        #just because I started naming the keys, with specid/quadid/type
        #i need to change that quadid so I can grab the tile from the datastore
        tmpK = key.split("/")
        tmpK[1] = tmpK[1]+str(qt)
        tmpK = '/'.join(tmpK)
        
        #grab it
        t = TmpTiles.get(db.Key.from_path('TmpTiles',"%s" % (tmpK)))
        #if there was no tile, it means that is an empty quarter of the tile we are creating, that is nice
        if t:
                
            #we need to do something kinda not obvious here
            #if the quad is 1 (top right) or 3 (bottom right)
            #we need to offset all column entries by 128
            oct = 0 if qt in [0,2] else 128
            #same if it is 2 or 3, we need to offset all rows by
            #128. This is to allow for each tile to fill up one
            #quarter of the new zoomed out tile (which is 256 in each direction)
            orow = 0 if qt in [0,1] else 128
            
            b = ''
            ct = 0
            #convert all the letters in the stored band back into a string of '1's and '0's
            for c in t.band:
                b += bDecode[c]
                
                
            ct = 0
            row = 0
            skip = True
            #iterate all charactters
            #but now I also do this funky math because I wanted to avoid turning
            #the string into a bunch of arrays, i thought this might save a bit of
            #time in the long run. It seems to work quickly, whether quicker or not is
            #another question.
            #but, 4 pixels from a higher resolution tile, will all be used to fill a 
            #single pixel in the lower resolution tile
            #something like:
            #low resolution '11
            #                11'
            #becomes a high resolution '1'
            #so i do that math.floor() to allow two rows and two columns to represent
            #a single row and a single same column in the low resolution
            #I then use those oct and orow offsets from above to shift them into the
            #correct corner of the tile that the high resolution tile describes
            #sorry, i realized i'm talking about them as 256x256 arrays, you can think
            #about them that way, i just use simple offsets instead of rows to get to 
            #the right data in a string 
            for c in b:
                if c != '0': #if the data is '0' we can skip anything, since '0' was the default in the n string we created above
                    n[oct+int(((math.floor(row/2)+orow)*256) + math.floor(ct/2))] = c
                    n[oct+int(((math.floor(row/2)+orow+1)*256) + math.floor(ct/2))] = c
                    n[oct+int(((math.floor(row/2)+orow)*256) + math.floor(ct/2) + 1)] = c
                    n[oct+int(((math.floor(row/2)+orow+1)*256) + math.floor(ct/2) + 1)] = c
                ct += 1
                if ct > 255:
                    row+=1
                    ct = 0
                
    #this guy i got of the webs, it just chunks a string into array of string length n, chk(str, n)
    chk = lambda v, l: [v[i*l:(i+1)*l] for i in range(int(math.ceil(len(v)/float(l))))]
        
    #logging.error(len(n))
    tmp = ''.join(n)
    tmp = chk(tmp,6)
    out = ''
    ct = 0
    #re-encode the byte string into our character string
    for z in tmp:
        ct+=1
        out += bEncode[int(z,2)]
    #and store
    tile = TmpTiles(key=db.Key.from_path('TmpTiles',key))
    tile.band = db.Text(out)
    tile.put()
                    
    
        
        
        
    
      
application = webapp.WSGIApplication(
         [('/api/taxonomy', Taxonomy),      
         ('/api/zoom/tiles', InterpolateTile),      
         ('/api/tile/[^/]+/[^/]+.png', Tile)],      
         debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
