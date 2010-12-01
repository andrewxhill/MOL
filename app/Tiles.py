from google.appengine.ext import db

class Tiles(db.Model):
    band = db.BlobProperty()
    
class TmpTiles(db.Model):
    band = db.TextProperty()
    
class TileUpdates(db.Model):
    when = db.DateTimeProperty(auto_now_add=True)
