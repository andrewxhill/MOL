from google.appengine.ext import db

class Tiles(db.Model):
    band = db.BlobProperty()
    
class TmpTiles(db.Model):
    keyLiteral = db.StringProperty()
    band = db.TextProperty()
