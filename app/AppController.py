import cgi, logging, png, copy
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

import os, string, Cookie, sha, time, random, cgi, urllib, datetime, cStringIO, pickle,random
import wsgiref.handlers

from COL import *

class DeleteBulk(webapp.RequestHandler):
  def get(self):
    self.post()
  def post(self):
    tb = self.request.get('tb',"default_db")
    q = db.GqlQuery("SELECT __key__ FROM %s" % tb)
    tot = 0
    r = q.fetch(300)
    tot = len(r)
    db.delete(r)
    if tot==300:
        taskqueue.add(url='/admin/bulkdelete', params={'tb': tb})
    return 200
    
class ColSearch(webapp.RequestHandler):
  def get(self):
    self.post()
  def post(self):
    cb = self.request.params.get('callback', None)
    if cb is not None:
        self.response.out.write("%s(" % cb)
    k = self.request.params.get('key', None)
    s = self.request.params.get('s', None)
    results = []
    c = self.request.params.get('cursor', None)
    #items = "{'items':["
    start = time.time()
    if k:
        key = db.Key.from_path('Species',k.lower())
        ent = Species.get(key)
        ele = k.split("/")
        r = {
             "rank": str(ele[-2]),
             "name": str(ele[-1]).replace("_"," "),
             "classification": simplejson.loads(ent.classification),
             "authority": simplejson.loads(ent.authority),
             "names": simplejson.loads(ent.names) #.replace('\\','')
            }
        results.append(r)
    elif s is not None:
        q = SpeciesIndex.gql("WHERE names = :1",s.lower())
        if c is not None:
            d = q.with_cursor(c).fetch(10)
        else:
            d = q.fetch(10)
        ct = 0
        for k in d:
            ct+=1
            key= k.key()
            ent = Species.get(key.parent())
            p= key.id_or_name().split('/')
            r = {
                 "rank": str(p[-2]),
                 "name": str(p[-1]).replace("_"," "),
                 "classification": simplejson.loads(ent.classification),
                 "authority": simplejson.loads(ent.authority),
                 "names": simplejson.loads(ent.names) #.replace('\\','')
                }
            results.append(r)
        if ct==10:
            c = q.cursor()
    
    t = int(1000*(time.time() - start))/1000.0
    #items += "'time': %s }" % t
    #self.response.out.write(json.loads(json.dumps(items)))
    out = {"time":t,"items":results,"cursor":c}
    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(simplejson.dumps(out, indent=4))
    if cb is not None:
        self.response.out.write(")")
        
    
    
class ColPage(webapp.RequestHandler):
  def get(self):
    path = os.path.join(os.path.dirname(__file__), 'templates/coltest.html')
    self.response.out.write(template.render(path, {}))
      
class MainPage(webapp.RequestHandler):
  def get(self):
    self.response.out.write('hi')
    
application = webapp.WSGIApplication(
         [('/', MainPage),
          ('/col', ColPage),
          ('/col/search', ColSearch),
          ('/admin/bulkdelete', DeleteBulk)],      
         debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
