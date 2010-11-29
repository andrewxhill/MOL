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
    
class ColPage(webapp.RequestHandler):
  def get(self):
    path = os.path.join(os.path.dirname(__file__), 'templates/coltest.html')
    self.response.out.write(template.render(path, {}))
      
class MainPage(webapp.RequestHandler):
  def get(self):
    self.response.out.write('hi')
    
application = webapp.WSGIApplication(
         [('/', MainPage),
          ('/playground/col', ColPage),
          ('/admin/bulkdelete', DeleteBulk)],      
         debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
