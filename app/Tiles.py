from google.appengine.ext import db
from google.appengine.api.labs import taskqueue
import time, datetime, logging
from google.appengine.api import memcache

class TileUpdate(db.Model):
    zoom = db.IntegerProperty()
    
class Tile(db.Model):
    band = db.BlobProperty()
    def put(self):
        memcache.set("tile-%s" % self.key().name(), self.band, 180)
        tmpK = self.key().name().split('/')
        tmpK[1] = tmpK[1][0:-1]
        zoom = len(tmpK[1])
        tmpK = '/'.join(tmpK)
        if zoom > 0:
            tmp = TileUpdate(key=db.Key.from_path('TileUpdate',tmpK))
            tmp.zoom = zoom
            tmp.put()
        return db.Model.put(self)
    
class TmpTile(db.Model):
    band = db.TextProperty()
    
