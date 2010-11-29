from google.appengine.ext import db

    
class SpeciesRanges(db.Model):
    rowid = db.IntegerProperty() #specid, see conversion table
    specid = db.IntegerProperty() #specid, see conversion table
    tilex = db.IntegerProperty() #osgeo
    osgeoy = db.IntegerProperty() #osgeo
    gmapy = db.IntegerProperty() #gmaps
    status = db.IntegerProperty() #1=present
    floatval = db.FloatProperty() #holds threshold values or other
    intval = db.IntegerProperty() #not sure yet
    zoom = db.IntegerProperty(default=9) #zoom level
    quad1 = db.IntegerProperty()
    quad2 = db.IntegerProperty()
    quad3 = db.IntegerProperty()
    quad4 = db.IntegerProperty()
    quad5 = db.IntegerProperty()
    quad6 = db.IntegerProperty()
    quad7 = db.IntegerProperty()
    quad8 = db.IntegerProperty()
    quad9 = db.IntegerProperty()
    quad10 = db.IntegerProperty()
    quad11 = db.IntegerProperty()
    quad12 = db.IntegerProperty()
    quad13 = db.IntegerProperty()
    quad14 = db.IntegerProperty()
    quad15 = db.IntegerProperty()
    quad16 = db.IntegerProperty()
    quad17 = db.IntegerProperty()
    quad18 = db.IntegerProperty()
    quad19 = db.IntegerProperty()
    quad20 = db.IntegerProperty()
