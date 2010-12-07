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
        tmp = TileUpdate(key=db.Key.from_path('TileUpdate',self.key().name()))
        tmp.zoom = len(self.key().name().split('/')[1])
        tmp.put()
        memcache.set("tile-%s" % self.key().name(), self.band, 180)
        return db.Model.put(self)
        
class Tiles(db.Model):
    band = db.BlobProperty()
    
class TmpTile(db.Model):
    band = db.TextProperty()
    
