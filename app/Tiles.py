from google.appengine.ext import db

class Tiles(db.Model):
    band = db.BlobProperty()
