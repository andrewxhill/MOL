from google.appengine.ext import db
import cgi, logging, png, copy, math, struct
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
    query = TileUpdates.all(keys_only=True).order("-zoom")
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
            name = "%s-%s%s-%d" % (name[0],name[1],name[2],int(now/10))
            try:
                taskqueue.add(
                    queue_name='tile-processing-queue',
                    url='/cron/interpolate/tiles',
                    params={'k': k, 'seed': seed},
                    name = '%s' % name,
                    eta = datetime.datetime.utcfromtimestamp(now) + datetime.timedelta(seconds=4))
            except:
                pass 
        else:
            k = '/'.join(k)
            db.delete(db.Key.from_path('TileUpdates',k))
    
      

class InterpolateTile(webapp.RequestHandler):
  def get(self):
    self.post()
  def post(self):
    oS = 3 #tells what band in the png is important. on appengine, it is the 4th band (oF=3) on localhost is is band 1,2 or 3 (I use oF=1)
    delList = []
    key = self.request.params.get('k', None)
    now = time.time()
    seed = self.request.params.get('seed', int(now/15))
    tile = Tiles.get(db.Key.from_path('Tiles',key))
    if tile: #if it does exist, turn it into a binary 256x256 matrix
        n = []
        for s in png.Reader(bytes=tile.band).asRGBA()[2]:
            n.append([0 if x in [0,'0'] else 1 for x in s[oS::4]])
    else: #if tile doesn't exist, create 256x256 matrix
        n = [[0 for i in range(256)] for i in range(256)]
        tile = Tiles(key=db.Key.from_path('Tiles',key))
    for qt in range(4): #cycle through each of the four higher resolution tiles that make up this single tile
        tmpK = key.split("/")
        tmpK[1] = tmpK[1]+str(qt)
        tmpK = '/'.join(tmpK)
        
        t = TileUpdates.get(db.Key.from_path('TileUpdates',tmpK))
        if t:
            t = Tiles.get(db.Key.from_path('Tiles',tmpK))
            delList.append(db.Key.from_path('TileUpdates',tmpK))
        orow = 0 if qt in [0,1] else 128 #row offset if the tile is either sub-quadtree 1,3
        ocol = 0 if qt in [0,2] else 128 #col offset if the tile is either sub-quadtree 2,3
        if t: 
            tmpI = images.Image(t.band)
            tmpI.resize(128,128)
            nt = png.Reader(bytes=tmpI.execute_transforms(output_encoding=images.PNG)).asRGBA8()
            
            #nt = png.Reader(bytes=images.resize(t.band,128,128)).asRGBA() #turn this sub-tile into 1/4 size so that it makes up only 1/4 of the lower resolution tile we are generating
            poss = []
            row = 0
            for s in nt[2]: #iterate through each of the 128 rows of the tile
                tmp = [0 if x in [0,'0'] else 1 for x in s[oS::4]] #turn the data into only the binary information based off the transparancy band (4) of the png ignoring the rgb bands (1,2,3)
                #tmp = ['0' if s[(4*x)] in [0,'0',0x00] else '1' for x in range((len(s)/4))] #turn the data into only the binary information based off the transparancy band (4) of the png ignoring the rgb bands (1,2,3)
                n[row+orow][ocol:ocol+128] = tmp
                row+=1
    db.delete(delList) #delete the sub-tiles from the TileUpdates table
    f = cStringIO.StringIO()
    palette=[(0xff,0xff,0xff,0x00),(0x00,0x00,0x00,0xff)]
    if oS == 1:
        palette=[(0x00,0x00,0x00,0xff),(0xff,0xff,0xff,0x00)]
    w = png.Writer(256,256, palette=palette, bitdepth=1)
    w.write(f, n)   
    tile.band = db.Blob(f.getvalue())
    tile.put()
    f.close()
    if len(key.split("/")[1]) > 1: #make sure we didn't just process the 0 level tile
        try:
            taskqueue.add(
                queue_name='tile-processing-queue',
                url='/cron/tileupdates',
                name = '%s-%s-%s' % (10,10,seed),
                eta = datetime.datetime.utcfromtimestamp(now) + datetime.timedelta(seconds=4))
            #logging.error(cursor)
        except:
            pass #allow the fail to happen quietly
    
    
class Bytes(webapp.RequestHandler):
  def get(self):
    oS = 1
    key = self.request.params.get('k', '1010/03232/pa')
    tile = Tiles.get(db.Key.from_path('Tiles',key))
    if 0 == 0x00:
        self.response.out.write('0 == 0x00')
    
    
    
    if tile: #if it does exist, turn it into a binary 256x256 matrix
        n = []
        row = 0
        for s in png.Reader(bytes=tile.band).asRGBA()[2]:
            n.append(['0' if x in [0,'0',0x00] else '1' for x in s[oS::4]])
            #n.append(['0' if s[(4*x)+3] in [0,'0',0x00] else '1' for x in range((len(s)/4))])
    else: #if tile doesn't exist, create 256x256 matrix
        n = [['0' for i in range(256)] for i in range(256)]
        tile = Tiles(key=db.Key.from_path('Tiles',key))
    for qt in range(4): #cycle through each of the four higher resolution tiles that make up this single tile
        tmpK = key.split("/")
        tmpK[1] = tmpK[1]+str(qt)
        tmpK = '/'.join(tmpK)
        
        t = Tiles.get(db.Key.from_path('Tiles',tmpK))
        orow = 0 if qt in [0,1] else 128 #row offset if the tile is either sub-quadtree 1,3
        ocol = 0 if qt in [0,2] else 128 #col offset if the tile is either sub-quadtree 2,3
        if t: 
            tmpI = images.Image(t.band)
            tmpI.resize(128,128)
            nt = png.Reader(bytes=tmpI.execute_transforms(output_encoding=images.PNG)).asRGBA()
            #nt = png.Reader().serialtoflat(bytes=tmpI.execute_transforms(output_encoding=images.PNG))
            self.response.out.write(nt)
            self.response.out.write("<br>")
            #nt = png.Reader(bytes=tmpI.execute_transforms(output_encoding=images.PNG)).asRGBA8() #turn this sub-tile into 1/4 size so that it makes up only 1/4 of the lower resolution tile we are generating
            
            poss = []
            row = 0
            for s in nt[2]: #iterate through each of the 128 rows of the tile
                
                self.response.out.write("%s: <br>" % row)
                self.response.out.write(s)
                self.response.out.write("<br>")
                #tmp = ['0' if s[(4*x)+3] == 0 else '1' for x in range((len(s)/4))] #turn the data into only the binary information based off the transparancy band (4) of the png ignoring the rgb bands (1,2,3)
                tmp = ['0' if x in [0,'0',0x00] else '1' for x in s[oS::4]] #turn the data into only the binary information based off the transparancy band (4) of the png ignoring the rgb bands (1,2,3)
                n[row+orow][ocol:ocol+128] = tmp
                row+=1
    ct = 0
    for i in n:
        self.response.out.write("%s: <br>" % ct)
        self.response.out.write(i)
        self.response.out.write("<br>")
        ct+=1
      
      

class SeeImage(webapp.RequestHandler):
  def get(self):
    oS = 1
    key = self.request.params.get('k', '1010/03232/pa')
    tile = Tiles.get(db.Key.from_path('Tiles',key))
    if tile: #if it does exist, turn it into a binary 256x256 matrix
        n = []
        row = 0
        for s in png.Reader(bytes=tile.band).asRGBA()[2]:
            n.append([0 if x in [0,'0',0x00] else 1 for x in s[oS::4]])
    else: #if tile doesn't exist, create 256x256 matrix
        n = [[1 for i in range(256)] for i in range(256)]
        tile = Tiles(key=db.Key.from_path('Tiles',key))
    for qt in range(4): #cycle through each of the four higher resolution tiles that make up this single tile
        tmpK = key.split("/")
        tmpK[1] = tmpK[1]+str(qt)
        tmpK = '/'.join(tmpK)
        
        t = Tiles.get(db.Key.from_path('Tiles',tmpK))
        
        orow = 0 if qt in [0,1] else 128 #row offset if the tile is either sub-quadtree 1,3
        ocol = 0 if qt in [0,2] else 128 #col offset if the tile is either sub-quadtree 2,3
        if t: 
            tmpI = images.Image(t.band)
            tmpI.resize(128,128)
            nt = png.Reader(bytes=tmpI.execute_transforms(output_encoding=images.PNG)).asRGBA8()
            #nbands = nt[3]['planes']
            #nt = png.Reader(bytes=images.resize(t.band,128,128)).asRGBA() #turn this sub-tile into 1/4 size so that it makes up only 1/4 of the lower resolution tile we are generating
            poss = []
            row = 0
            for s in nt[2]: #iterate through each of the 128 rows of the tile
                tmp = [0 if x in [0,'0',0x00] else 1 for x in s[oS::4]] #turn the data into only the binary information based off the transparancy band (4) of the png ignoring the rgb bands (1,2,3)
                n[row+orow][ocol:ocol+128] = tmp
                row+=1
    
    f = cStringIO.StringIO()
    palette=[(0xff,0xff,0xff,0x00),(0x00,0x00,0x00,0xff)]
    if oS == 1:
        palette=[(0x00,0x00,0x00,0xff),(0xff,0xff,0xff,0x00)]
    
    #palette=[(0xff),(0x00)]
    w = png.Writer(256,256, palette=palette, bitdepth=1)
    #w = png.Writer(256,256, transparent=1, greyscale=True)
    w.write(f, n)   
    
    self.response.headers['Content-Type'] = "image/png"
    self.response.out.write(f.getvalue())
    
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
