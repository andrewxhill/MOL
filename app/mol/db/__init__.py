#!/usr/bin/env python
#
# Copyright 2010 Andrew W. Hill, Aaron Steele
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from google.appengine.ext import db
from ndb import model

class MetaData(db.Model):
    object = db.TextProperty()
    parentKey = db.StringProperty()
    
class MetaDataIndex(db.Expando): #parent=MetaData
    """Index relation entity for MetaData."""
    data_name = db.StringProperty()
    data_source = db.StringProperty()
    keywords = db.StringListProperty()
  
class MasterSearchIndex(db.Model): #parent = OccurrenceSet or MultiPolygon (see below)
    term = db.CategoryProperty() #string values to search for sets
    rank = db.RatingProperty(default=0) #weight of term for an order by
  
class OccurrenceSetIndex(db.Model): #parent = OccurrenceSet see below
    term = db.CategoryProperty() #string values to search for sets
    rank = db.RatingProperty(default=0) #weight of term for an order by
    
class OccurrenceSet(db.Model): #key_name = ecoregion/wwf/puma_concolor or something
    name = db.StringProperty() #this could be non-unique, Puma concolor is fine
    subname = db.StringProperty()
    source = db.CategoryProperty() #wwf
    category = db.CategoryProperty() #ecoregion
    info = db.TextProperty() #some meta standard for sets of occ polygons
    dateCreated = db.DateTimeProperty(auto_now_add=True)
    
class OccurrenceIndex(db.Model): #parent = MultiPolygon see below
    introduced = db.BooleanProperty(default=None) 
    deleted = db.BooleanProperty(default=None) 
    occurrenceSet = db.ReferenceProperty(OccurrenceSet, collection_name="polygons") #OccurrenceSet
    
class MultiPolygonIndex(db.Model): #parent = MultiPolygon see below
    term = db.CategoryProperty() #string values to search for sets
    rank = db.RatingProperty(default=0) #weight of term for an order by
    
class MultiPolygon(db.Model): #key_name = some_id
    name = db.StringProperty()
    subname = db.StringProperty()
    source = db.CategoryProperty() #'wwf' would be one
    category = db.CategoryProperty() #'ecoregion' would be one
    info = db.TextProperty(default=None) #some meta standard based on the type, but not restriced by the datastore model
    dateCreated = db.DateTimeProperty(auto_now_add=True)

class Tile(db.Model):
    band = db.BlobProperty()

class Species(db.Model):
    authority = db.TextProperty()
    classification = db.TextProperty()
    names = db.TextProperty()

class SpeciesIndex(db.Model):
    names = db.StringListProperty()
    authorityName = db.StringProperty()
    authorityIdentifier = db.StringProperty()
    kingdom = db.StringProperty()
    phylum = db.StringProperty()
    class_ = db.StringProperty()
    order_ = db.StringProperty()
    superFamily = db.StringProperty()
    family = db.StringProperty()
    genus = db.StringProperty()
    species = db.StringProperty()
    infraSpecies = db.StringProperty()
    hasRangeMap = db.BooleanProperty(default=False)


    
