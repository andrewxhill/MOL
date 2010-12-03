from google.appengine.ext import db

class Tiles(db.Model):
    band = db.BlobProperty()
    
class TmpTiles(db.Model):
    band = db.TextProperty()
    
class TileUpdates(db.Model):
    zoom = db.IntegerProperty()
