from google.appengine.ext import db
import cgi, logging, png, copy, math, struct
from django.utils import simplejson

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api.labs import taskqueue
from google.appengine.api import memcache
from google.appengine.ext.webapp import template
from google.appengine.api import images
from google.appengine.api import quota

from mapreduce import control as mr_control 

import os, string, Cookie, sha, time, random, cgi
import urllib, datetime, cStringIO, pickle,random
import wsgiref.handlers
import cStringIO, png

from COL import *
from Tiles import *


class Updates(webapp.RequestHandler):
  def post(self):
    self.get()
  def get(self):
    now = time.time()
    seed = int(now)
    #if it is kicked of by the cron, create 10 tasks
    query = TileUpdate.all(keys_only=True).order("-zoom")
    #if cursor is not None:
    changed = query.fetch(400)
    #cursor = query.cursor()
    for c in changed:
        k = c.name()
        k = k.split("/")
        #make sure it isn't a 0 level tile
        if len(k[1]) > 1:
            #remove the last number in the quadid to get the quadid of the lower resolution tile that owns it
            k[1] = k[1][:-1]
            #put the array back together
            k = '/'.join(k)
            #if task for this key already exists, it will fail
            name = k.split('/')
            name = "%s-%s%s-%d" % (name[0], name[1], name[2], int(now / 10))
            try:
                taskqueue.add(
                    queue_name='tile-processing-queue',
                    url='/cron/interpolate/tiles',
                    params={'k': k, 'seed': seed},
                    name='%s' % name,
                    eta=datetime.datetime.utcfromtimestamp(now) + datetime.timedelta(seconds=4))
            except:
                pass
        else:
            k = '/'.join(k)
            db.delete(db.Key.from_path('TileUpdate', k))



class InterpolateTile(webapp.RequestHandler):
  def get(self):
    self.post()
  def post(self):
    delList = []
    key = self.request.params.get('k', None)
    now = time.time()
    seed = self.request.params.get('seed', int(now / 15))
    tile = Tile.get(db.Key.from_path('Tile', key))
    if tile: #if it does exist, turn it into a binary 256x256 matrix
        n = []
        row = 0
        for s in png.Reader(bytes=tile.band).asRGBA8()[2]:
            n.append(list(s))
    else: #if tile doesn't exist, create 256x256 matrix
        n = [[0 for i in range(256*4)] for i in range(256)]
        tile = Tile(key=db.Key.from_path('Tile',key))
    for qt in range(4): #cycle through each of the four higher resolution tiles that make up this single tile
        tmpK = key.split("/")
        tmpK[1] = tmpK[1]+str(qt)
        tmpK = '/'.join(tmpK)
        t = TileUpdate.get(db.Key.from_path('TileUpdate', tmpK))
        band = None
        if t:
            band = memcache.get("tile-%s" % tmpK)
            if band is None:
                t = Tile.get(db.Key.from_path('Tile', tmpK))
                if t is not None:
                    band = t.band
            delList.append(db.Key.from_path('TileUpdate', tmpK))
        orow = 0 if qt in [0,1] else 128 #row offset if the tile is either sub-quadtree 1,3
        ocol = 0 if qt in [0,2] else 128 #col offset if the tile is either sub-quadtree 2,3
        if band: 
            poss = []
            row = 0
            for s in png.Reader(bytes=images.resize(band,128,128)).asRGBA8()[2]: #iterate through each of the 128 rows of the tile
                n[row+orow][4*ocol:4*(ocol+128)] = list(s)
                row+=1
                
    db.delete(delList) #delete the sub-tiles from the TileUpdates table
    f = cStringIO.StringIO()
    w = png.Writer(256,256, planes=4, alpha=True, greyscale=False, bitdepth=8)
    #w.write_array(f,n)
    w.write_passes(f,n,packed=False)
    tile.band = db.Blob(f.getvalue())
    tile.put()
    f.close()
    if len(key.split("/")[1]) > 1: #make sure we didn't just process the 0 level tile
        try:
            taskqueue.add(
                queue_name='tile-processing-queue',
                url='/cron/tileupdates',
                name='%s-%s-%s' % (10, 10, seed),
                eta=datetime.datetime.utcfromtimestamp(now) + datetime.timedelta(seconds=4))
        except:
            pass #allow the fail to happen quietly
    
    
class Bytes(webapp.RequestHandler):
  def get(self):
    oS = 3
    key = self.request.params.get('k', '1010/03232/pa')
    tile = Tile.get(db.Key.from_path('Tile',key))
    
    
    if tile: #if it does exist, turn it into a binary 256x256 matrix
        n = []
        row = 0
        for s in png.Reader(bytes=tile.band).asRGBA8()[2]:
            n.append(list(s))
            #n.append([(s[(x*4)],s[(x*4)+1],s[(x*4)+2],s[(x*4)+3]) for x in range(int(len(s)/4))])
            #n.append(['0' if s[(4*x)+3] in [0,'0',0x00] else '1' for x in range((len(s)/4))])
    else: #if tile doesn't exist, create 256x256 matrix
        n = [[0 for i in range(256*4)] for i in range(256)]
        tile = Tile(key=db.Key.from_path('Tile',key))
    for qt in range(4): #cycle through each of the four higher resolution tiles that make up this single tile
        tmpK = key.split("/")
        tmpK[1] = tmpK[1]+str(qt)
        tmpK = '/'.join(tmpK)
        
        t = Tile.get(db.Key.from_path('Tile',tmpK))
        orow = 0 if qt in [0,1] else 128 #row offset if the tile is either sub-quadtree 1,3
        ocol = 0 if qt in [0,2] else 128 #col offset if the tile is either sub-quadtree 2,3
        if t: 
            nt = png.Reader(bytes=images.resize(t.band,128,128)).asRGBA8()
            #nt = png.Reader().serialtoflat(bytes=tmpI.execute_transforms(output_encoding=images.PNG))
            self.response.out.write(nt)
            self.response.out.write("<br>")
            #nt = png.Reader(bytes=tmpI.execute_transforms(output_encoding=images.PNG)).asRGBA8() #turn this sub-tile into 1/4 size so that it makes up only 1/4 of the lower resolution tile we are generating
            
            poss = []
            row = 0
            for s in nt[2]: #iterate through each of the 128 rows of the tile
                tmp = list(s)
                #tmp = [(s[(x*4)],s[(x*4)+1],s[(x*4)+2],s[(x*4)+3]) for x in range(int(len(s)/4))]
                self.response.out.write("%s: <br>" % row)
                self.response.out.write(tmp)
                self.response.out.write("<br>")
                #tmp = ['0' if s[(4*x)+3] == 0 else '1' for x in range((len(s)/4))] #turn the data into only the binary information based off the transparancy band (4) of the png ignoring the rgb bands (1,2,3)
                #tmp = ['0' if x in [0,'0',0x00] else '1' for x in s[oS::4]] #turn the data into only the binary information based off the transparancy band (4) of the png ignoring the rgb bands (1,2,3)
                n[row+orow][4*ocol:4*(ocol+128)] = tmp
                row+=1
    ct = 0
    for i in n:
        self.response.out.write("%s: <br>" % ct)
        self.response.out.write(i)
        self.response.out.write("<br>")
        ct+=1
      
      

class SeeImage(webapp.RequestHandler):
  def get(self):
    #oS = 1
    key = self.request.params.get('k', '1010/03232/pa')
    tile = Tile.get(db.Key.from_path('Tile',key))
    if tile: #if it does exist, turn it into a binary 256x256 matrix
        n = []
        row = 0
        for s in png.Reader(bytes=tile.band).asRGBA8()[2]:
            n.append(list(s))
            #n.append([(s[(x*4)],s[(x*4)+1],s[(x*4)+2],s[(x*4)+3]) for x in range(int(len(s)/4))])
            #n.append(['0' if s[(4*x)+3] in [0,'0',0x00] else '1' for x in range((len(s)/4))])
    else: #if tile doesn't exist, create 256x256 matrix
        n = [[0 for i in range(256*4)] for i in range(256)]
        tile = Tile(key=db.Key.from_path('Tile',key))
        
    for qt in range(4): #cycle through each of the four higher resolution tiles that make up this single tile
        tmpK = key.split("/")
        tmpK[1] = tmpK[1]+str(qt)
        tmpK = '/'.join(tmpK)
        
        t = Tile.get(db.Key.from_path('Tile',tmpK))
        
        orow = 0 if qt in [0,1] else 128 #row offset if the tile is either sub-quadtree 1,3
        ocol = 0 if qt in [0,2] else 128 #col offset if the tile is either sub-quadtree 2,3
        if t: 
            nt = png.Reader(bytes=images.resize(t.band,128,128)).asRGBA8()
            #nbands = nt[3]['planes']
            #nt = png.Reader(bytes=images.resize(t.band,128,128)).asRGBA() #turn this sub-tile into 1/4 size so that it makes up only 1/4 of the lower resolution tile we are generating
            poss = []
            row = 0
            for s in nt[2]: #iterate through each of the 128 rows of the tile
                #tmp = [1 if s[(x*4)]==s[(x*4)+1]==s[(x*4)+2]==s[(x*4)+3] else 0 for x in range(int(len(s)/4))]
                #tmp = list(s)
                tmp = list(s)
                #tmp = [(s[(x*4)],s[(x*4)+1],s[(x*4)+2],s[(x*4)+3]) for x in range(int(len(s)/4))]
                n[row+orow][(4*ocol):4*(ocol+128)] = tmp
                row+=1
    
    f = cStringIO.StringIO()
    
    #palette=[(0,0,0,0),(0,0,0,255)]
    w = png.Writer(256,256, planes=4, alpha=True, greyscale=False, bitdepth=8)
    #w.write_array(f,n)
    w.write_passes(f,n,packed=False)
    #w = png.Writer(256,256, interlace=0, palette=palette, bitdepth=1, greyscale=False)
    #w = png.Writer(256,256, transparent=1, greyscale=True)
    #w.write(f, n)   
    
    self.response.headers['Content-Type'] = "image/png"
    self.response.out.write(f.getvalue())
    
class DeleteBulk(webapp.RequestHandler):
  def get(self):
    self.post()
  def post(self):
    tb = self.request.get('tb',None)
    if tb is None:
        tc = self.request.get('tc','TileUpdates')
        q = db.GqlQuery("SELECT __key__ FROM %s" % tc).fetch(20)
        for a in q:
            self.response.out.write(a.name())
            self.response.out.write("<br>")
    else:
        q = db.GqlQuery("SELECT __key__ FROM %s" % tb)
        tot = 0
        r = q.fetch(300)
        tot = len(r)
        db.delete(r)
        if tot==300:
            taskqueue.add(url='/admin/bulkdelete', params={'tb': tb})
        return 200

application = webapp.WSGIApplication(
         [('/cron/tileupdates', Updates),
         ('/cron/see', SeeImage),      
         ('/cron/interpolate/tiles', InterpolateTile),      
         ('/cron/bytes', Bytes)],      
         debug=True)


def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()

