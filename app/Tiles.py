from google.appengine.ext import db
from google.appengine.api.labs import taskqueue
import time, datetime, logging

class TileUpdates(db.Model):
    zoom = db.IntegerProperty()
    
class Tiles(db.Model):
    band = db.BlobProperty()
    def put(self):
        tmp = TileUpdates(key=db.Key.from_path('TileUpdates',self.key().name()))
        tmp.zoom = len(self.key().name().split('/')[1])
        tmp.put()
        return db.Model.put(self)
    
class TmpTiles(db.Model):
    band = db.TextProperty()
    
