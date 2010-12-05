#!/usr/bin/env python
#
# Copyright 2010 Map Of Life
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from google.appengine.api import images
from google.appengine.api.labs import taskqueue
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from mol.db import Tile, TileUpdate
import datetime
import png
import time
import cStringIO

class Updates(webapp.RequestHandler):

  def post(self):
    self.get()

  def get(self):
    now = time.time()
    seed = int(now)
    #if it is kicked of by the cron, create 10 tasks
    query = TileUpdate.all(keys_only=True).order("-zoom")
    #if cursor is not None:
    #    query.with_cursor(cursor)
    changed = query.fetch(100)
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
            name = "%s-%s-%d" % (name[0], name[1], int(now / 10))
            try:

                taskqueue.add(
                    queue_name='tile-processing-queue',
                    url='/cron/interpolate/tiles',
                    params={'k': k, 'seed': seed},
                    name='%s' % name,
                    eta=datetime.datetime.utcfromtimestamp(now) + datetime.timedelta(seconds=1))
                #logging.error(k)
            except:
                pass
                #logging.error('new tileupdates failed: %s' % inst)
        else:
            k = '/'.join(k)
            db.delete(db.Key.from_path('TileUpdate', tmpK))

class InterpolateTile(webapp.RequestHandler):

  def get(self):
    self.post()

  def post(self):
    #from now on, assume the key sent was k="01"
    key = self.request.params.get('k', None)
    seed = self.request.params.get('seed', int(time.time() / 15))
    now = time.time()
    delList = []

    n = [[] for i in range(256)]

    for qt in range(4):
        tmpK = key.split("/")
        tmpK[1] = tmpK[1] + str(qt)
        tmpK = '/'.join(tmpK)

        #delete record if it is in the TileUpdates kind
        delList.append(db.Key.from_path('TileUpdate', tmpK))

        t = Tile.get(db.Key.from_path('Tile', tmpK))

        orow = 0 if qt in [0, 1] else 128
        ocol = 0 if qt in [0, 2] else 128

        if t:
            nt = png.Reader(bytes=images.resize(t.band, 128, 128)).asRGBA()
            row = 0
            for s in nt[2]:
                ct = 0
                while ct < len(s):
                    if s[ct] != 0:
                        n[row + orow].append(u'1')
                    else:
                        n[row + orow].append(u'0')
                    ct += 4
                row += 1
        else:
            for r in range(orow, orow + 128):
                for c in range(128):
                    n[r].append(u'0')


    #delete any tiles processed above
    db.delete(delList)

    f = cStringIO.StringIO()
    palette = [(0xff, 0xff, 0xff, 0x00), (0x00, 0x00, 0x00, 0xff)]
    w = png.Writer(256, 256, palette=palette, bitdepth=1)
    w.write(f, n)

    #and store
    tile = Tile(key=db.Key.from_path('Tiles', key))
    tile.band = db.Blob(f.getvalue())
    tile.put()
    f.close()

    #make sure it isn't a 0 level tile
    if len(key.split("/")[1]) > 1:
        #up = TileUpdates(key=db.Key.from_path('TileUpdates',key))
        #putList.append(up)
        #if task for this key already exists but hasn't executed, it will fail
        try:
            taskqueue.add(
                queue_name='tile-processing-queue',
                url='/cron/tileupdates',
                name='%s-%s-%s' % (10, 10, seed),
                eta=datetime.datetime.utcfromtimestamp(now) + datetime.timedelta(seconds=2))
            #logging.error(cursor)
        except:
            #allow the fail to happen quietly
            pass


application = webapp.WSGIApplication(
         [('/cron/tileupdates', Updates),
         ('/cron/interpolate/tiles', InterpolateTile)],
         debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
