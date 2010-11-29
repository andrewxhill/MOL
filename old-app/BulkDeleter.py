import cgi
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import memcache, urlfetch
from google.appengine.api.labs import taskqueue

import os, sys, string

from wsgiref.handlers import CGIHandler
import logging

#project module storing all the db table models
from DataStore import *

def wsgi_app(env, res):
    q = SpeciesRanges.all()
    for i in q.fetch(999):
        i.delete()
    
    p = p[0]
    endtime = p.EndTime
    cur = ''
    d = datetime.timedelta(hours=2)
    if endtime < datetime.datetime.now()+d:
        n = ProductQueue.gql("WHERE Position > 0 ORDER BY Position ASC").fetch(1)
        n = int(n[0].Position)
        q = ProductQueue.all()
        tot = 0
        for i in q.fetch(999):
            i.Position = i.Position - n
            i.put()
            tot+=1
        cur = q.cursor()
        if tot==999:
            taskqueue.add(url='/admin/private/queueupdate', params={'cursor': cur,'n': n})
            
        
    res('200 OK',[('Content-Type','text/plain')])
    return ['queue updated' + str(tot)]
    
def main():
    CGIHandler().run(wsgi_app)

if __name__ == '__main__':
    main()





