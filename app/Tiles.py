from google.appengine.ext import db

class Tiles(db.Model):
    band = db.BlobProperty()
    
class TmpTiles(db.Model):
    band = db.TextProperty()
