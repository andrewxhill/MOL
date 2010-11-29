import cgi

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api.labs import taskqueue
from google.appengine.api import memcache
from google.appengine.ext.webapp import template
from google.appengine.api import images

import os, string, Cookie, sha, time, random, cgi, urllib, datetime, StringIO, pickle,random
import wsgiref.handlers
import logging, png, copy

from DataStore import *

#TILE_CACHE_TIME = 43200 #in seconds
TILE_CACHE_TIME = 345600 #in seconds
#TILE_CACHE_TIME = 0 #in seconds
ZOOM_LEVEL = 11
GTILE = 100000001
PIXELS = 256

def TileArray(ro,co,default='1'):
    b = []
    for i in range(ro):
        b.append([default for j in range(co)])
    return b


    
    
class BigQuery(object):
    def __init__(self, id, z, q, x, y):
        
        if z == ZOOM_LEVEL:
            gql = "WHERE specid = %i AND quad%i = %i" % (int(id),int(z),int(q))
            qu = SpeciesRanges.gql(gql)
            if qu.count() == 1:
                self.img = 1
            else:
                self.img = 0
        elif z > ZOOM_LEVEL:
            while len(q) > z:
                q = list(q)
                q = ''.join(q[:-2])
            gql = "WHERE specid = %i AND quad%i = %i" % (int(id),int(ZOOM_LEVEL),int(q))
            qu = SpeciesRanges.gql(gql)
            if qu.count() == 1:
                self.img = 1
            else:
                self.img = 0
        else:
            mt = True #the image is empty of any pixels
            dim = 1 << z #w=h, number of tiles per row or column of global map
            tpix = 1 << ZOOM_LEVEL #number of pixels/row available given zoom
            cpix = tpix/dim #number of pixels per row for a single tile
            mpix = cpix/PIXELS #the modification number for the pixel -> matrix conversion
            try:
                mopix = PIXELS/cpix
            except:
                mopix = 0
                
            th = cpix * cpix
            default='1'
            self.b = TileArray(PIXELS,PIXELS)
            
            self.img = 0
            
            gql = "WHERE specid = %i AND quad%i = %i" % (int(id),int(z),int(q))
            qu = SpeciesRanges.gql(gql)
            ct = qu.count()
            if ct == th:
                self.img = 1
            elif ct == 0: pass
            else:
                rows = qu.fetch(999)
                tot = 999
                i = 0
                out = ''
                while tot==999:
                    tot = 0
                    for r in rows:
                        #convert to local offset from global offset
                        y = r.gmapy if r.gmapy <= cpix else r.gmapy - ((r.gmapy/cpix) * cpix) 
                        #while r.gmapy > cpix: r.gmapy = r.gmapy - cpix 
                        x = r.tilex if r.tilex <= cpix else r.tilex - ((r.tilex/cpix) * cpix)
                        #while r.tilex > cpix: r.tilex = r.tilex - cpix
                        
                        if 0<mpix:
                            self.b[y/mpix][x/mpix] = '0'
                        else:
                            i = 0
                            while i < mopix:
                                j = 0
                                
                                while j < mopix:
                                    self.b[(mopix*y)+i][(mopix*x)+j] = '0'
                                    j+=1
                                
                                i+=1
                            
                        mt = False
                        tot += 1
                    if tot==999:
                        cur = qu.cursor()
                        rows = qu.with_cursor(cur).fetch(999)
                #return b
                
                if mt: pass
                else:
                    f = StringIO.StringIO()
                    p = png.Writer(PIXELS,PIXELS, greyscale=True, bitdepth=1, transparent=(0xff))
                    p.write(f,self.b)
                    self.img = f.getvalue()

class APIGetTile(webapp.RequestHandler):
  def get(self):
      self.post()
  def post(self):
    pass
    
class MainPage(webapp.RequestHandler):
  def get(self):
    self.response.out.write('hi')
    
class DemoPage(webapp.RequestHandler):
  def get(self):
    id = self.request.params.get('id', GTILE)
    template_values = {
                "specid": id
            }
    path = os.path.join(os.path.dirname(__file__), 'templates/demo.html')
    self.response.out.write(template.render(path, template_values))
    
    
class PreCache(webapp.RequestHandler):
  def get(self):
      self.post()
  def post(self):
    id = self.request.params.get('id', 8)
    z = int(self.request.params.get('z', 8)) #what zoom level we are working at
    x = int(self.request.params.get('x', 0)) #tile x number to check
    y = int(self.request.params.get('y', 0)) #tile y number to check
    empty = int(self.request.params.get('empty', False)) #tile y number to check
    q = getQuadTree(x,y,z)
    
    for i in [0,1,2,3]:
        q += "%s" % i
        nx,ny,nz = getXYZ(q,z+1)
        k = "id:%s;q:%s;" % (id,q)
        p = memcache.get(k)
        if p is not None:
            memcache.set(k, p, TILE_CACHE_TIME/(z+1))
        else:
            if empty is False:
                taskqueue.add(url='/tile', params={'id': id,'x': nx,'y': ny,'z': nz,'empty': 1})
            else:
                p = 0
                memcache.set(k, p, TILE_CACHE_TIME/(z+1))
    pass
    
    
def getXYZ(quad,zoom=1):
    quad = str(quad)
    while len(quad) < zoom:
        quad = "0"+quad
    z = 1
    wx = {'0':0,'1':1,'2':0,'3':1}
    wy = {'0':0,'1':0,'2':1,'3':1}
    t = (1<<len(quad)-1)
    vx = 0
    vy = 0
    for c in quad[:]:
        vx += wx[c] * t
        vy += wy[c] * t
        t = t/2
    return vx,vy,len(quad)
    
def getQuadTree(x,y,z):
    i = 1
    last = 0
    div = (1 << (z-1))
    q = ''
    while i<=z:
        m = (1 << (i-1))
        d = div/m #256
        if last in [1,3]:
            x = x - 2*d #415
        if last in [2,3]:
            y = y - 2*d #305
        c = 0
        if x > d-1: c = c+1 
        if y > d-1: c = c+2 
        q += str(c)
        last = c
        i+=1
    return q
    

class TileQuery(webapp.RequestHandler):
  def get(self):
      self.post()
  def post(self):
    #memcache.flush_all()
    
    id = int(self.request.params.get('id', GTILE)) #what zoom level we are working at
    
    z = int(self.request.params.get('z', 1)) #what zoom level we are working at
    z += (256/PIXELS) - 1
    
    x = int(self.request.params.get('x', 0)) #tile x number to check
    y = int(self.request.params.get('y', 0)) #tile y number to check
    
    m = self.request.params.get('m', 'gmaps') #tile number is google maps or osgeo map number
    y = ((1 << z) - y - 1) if str(m)=='osgeo' else y #convert to osgeo tile numbering if needed
    
    q = getQuadTree(x,y,z) #get QuadTree key for tile
    
    k = "id:%s;q:%s;" % (id,q)
    p = memcache.get(k)
    
    c = True
    if p is None:
        p = BigQuery(id,z,q,x,y).img
        c = False
    memcache.set(k, p, TILE_CACHE_TIME/(z+1))
    
    if self.request.params.get('empty', False) is False: 
        if p == 0: #indicates completely empty tile
            if not c:
                taskqueue.add(url='/precache', params={'id': id,'z': z,'x': x,'y': y,'empty': 1})
            self.redirect('/static/none.png')
        elif p == 1: #indicates completely full tile
            if not c:
                taskqueue.add(url='/precache', params={'id': id,'z': z,'x': x,'y': y})
            self.redirect('/static/tile.png')
        else:
            if not c:
                taskqueue.add(url='/precache', params={'id': id,'z': z,'x': x,'y': y})
            self.response.headers['Content-Type'] = 'image/png'
            self.response.out.write(p)
    else:
        pass
    
class FlushCache(webapp.RequestHandler):
  def get(self):
    memcache.flush_all()
    pass
    
class ImageTest(webapp.RequestHandler):
  def get(self):
    n = int(self.request.params.get('n', 1))
    t=0
    while t < n:
        b = []
        i = 0
        ystop = 256
        xstop = 256
        while i<256:
            a = 0
            s = ''
            while a < 256:
                if a<ystop:
                    s += '0'
                    if random.random()>0.9999:
                        ystop = a
                else:
                    s += '1'
                a+=1
            b.append(s)
            i+=1
        b = map(lambda x: map(int, x), b)
        
        f = StringIO.StringIO()
        p = png.Writer(256,256, greyscale=True, bitdepth=1, transparent=(0xff))
        p.write(f,b)
        t+=1
    self.response.headers['Content-Type'] = 'image/png'
    self.response.out.write(f.getvalue())
    
class CheckStore(webapp.RequestHandler):
  def get(self):
    id = 100000001
    x = 3
    y = 1
    z = 2
    q = 13
    #a = BigQuery(id, z, q, x, y)
    
    id = int(self.request.params.get('id', GTILE))
    #q = SpeciesRanges.gql("WHERE specid = :sid AND quad2 = :quad ORDER BY quad11", quad=quad, sid=id).fetch(999)
    #q = SpeciesRanges.all().fetch(25)
    qu = "WHERE specid = %i AND quad%i = %i" % (int(id),int(z),int(q))
    q = SpeciesRanges.gql(qu).fetch(25)
    out = 'Hello<br>'
    for s in q:
        out += "%s<br>\n" % ','.join([str(i) for i in [s.specid,s.quad3,x,y,z]])
    self.response.out.write(out+str(len(q)))
    
    #self.response.out.write(a.b)
    """
    rowid,specid,tilex,tiley,status,floatval,intval,zoom
    rowid,specid,tilex,tiley,status,floatval,intval,zoom,quad1,quad2,quad3,quad4,quad5,quad6,quad7,quad8,quad9
    ../xgoogle_appengine/appcfg.py upload_data --num_threads=2 --filename=dbfile.tmp.csv --kind=SpeciesRanges  --url=http://localhost:8080/remote_api --application=mol-apps --config_file=bulkmol.yaml --batch_size=250 molapps/
    """
        
class DeleteBulk(webapp.RequestHandler):
  def get(self):
    self.post()
  def post(self):
    cur = self.request.get('cursor',None)
    q = SpeciesRanges.all()
    if cur is not None:
        q.with_cursor(cur)
    tot = 0
    for i in q.fetch(300):
        i.delete()
        tot+=1
    cur = q.cursor()
    if tot==300:
        taskqueue.add(url='/admin/bulkdelete', params={'cursor': cur})
    return 200
    
    
application = webapp.WSGIApplication(
         [('/', MainPage),
          ('/demo', DemoPage),
          ('/tile', TileQuery),
          ('/store', CheckStore),
          ('/precache', PreCache),
          ('/admin/image', ImageTest),
          ('/admin/flush', FlushCache),
          ('/admin/bulkdelete', DeleteBulk)],      
         debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
