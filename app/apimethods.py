from google.appengine.ext import db
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

class Taxonomy(webapp.RequestHandler):
  def methods(self):
    out = {"methods":{
        "search": "provide a name string to search for",
        "rank": "indicate the name rank to search in, default genus species",
        "key": "provide the known key for a taxon 'animalia/rank/binomial'",
        "callback": "crossdomain callback name",
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
            q = SpeciesIndex.gql("WHERE names = :1 ORDER BY %s" % orderOn, s.lower())
        else:
            q = SpeciesIndex.gql("WHERE %s = :1 ORDER BY %s" % (rank,orderOn), s.lower())
        d = q.fetch(n,offset=of)
    memcache.set(memk,d,3000)
    ct = 0
    for k in d:
        ct+=1
        key= k.key()
        ent = Species.get(key.parent())
        p= key.id_or_name().split('/')
        e = {
             "rank": str(p[-2]),
             "name": str(p[-1]).replace("_"," "),
             "classification": simplejson.loads(ent.classification),
             "authority": simplejson.loads(ent.authority),
             "names": simplejson.loads(ent.names) #.replace('\\','')
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
    self.response.out.write(simplejson.dumps(out))
    if cb is not None:
        self.response.out.write(")")
        
    
    
application = webapp.WSGIApplication(
         [('/api/taxonomy', Taxonomy)],      
         debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
