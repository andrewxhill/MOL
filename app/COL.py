from google.appengine.ext import db

#This is the datastore model that is needed in your App to use the bulk loader
#We will be working to optimize and error check all of this as we go.
class Species(db.Model):
    authority = db.TextProperty()
    classification = db.TextProperty()
    names = db.TextProperty()
    
class SpeciesIndex(db.Model):
    names = db.StringListProperty()
    authorityName = db.StringProperty()
    kingdom = db.StringProperty()
    phylum = db.StringProperty()
    class_ = db.StringProperty()
    order_ = db.StringProperty()
    superFamily = db.StringProperty()
    family = db.StringProperty()
    genus = db.StringProperty()
    species = db.StringProperty()
    infraSpecies = db.StringProperty()
    
