#!/usr/bin/env python
#
# Copyright 2010 Map Of Life
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


class OccurrenceSetIndex(db.Model): #parent = OccurrenceSet see below
    term = db.CategoryProperty() #string values to search for sets
    rank = db.RatingProperty(default=0) #weight of term for an order by
    
class OccurrenceSet(db.Model): #key_name = ecoregion/wwf/puma_concolor or something
    name = db.StringProperty() #this could be non-unique, Puma concolor is fine
    source = db.StringProperty() #wwf
    type = db.StringProperty() #ecoregion
    info = db.BlobProperty() #some meta standard for sets of occ polygons
    dateCreated = db.DateTimeProperty(auto_now_add=True)
    
class OccurrenceIndex(db.Model): #parent = MultiPolygon see below
    occurrenceSetKey = db.StringProperty() #key_name string
    introduced = db.BooleanProperty(default=None) 
    deleted = db.BooleanProperty(default=None) 
    occurrenceSet = db.ReferenceProperty(OccurrenceSet, collection_name="polygons") #OccurrenceSet
    
class MultiPolygonIndex(db.Model): #parent = OccurrenceSet see below
    term = db.CategoryProperty() #string values to search for sets
    rank = db.RatingProperty(default=0) #weight of term for an order by
    
class MultiPolygon(db.Model): #key_name = some_id
    name = db.StringProperty()
    subname = db.StringProperty()
    type = db.CategoryProperty() #'ecoregion' would be one
    source = db.CategoryProperty() #'wwf' would be one
    info = db.BlobProperty() #some meta standard based on the type, but not restriced by the datastore model
    dateCreated = db.DateTimeProperty(auto_now_add=True)

#all the info about the Ecoregion polygons
class Ecoregion(db.Model): #key_name = ('Ecoregion', eco_code)
    ecoName = db.StringProperty()
    realm = db.StringProperty()
    biome = db.IntegerProperty()
    ecoNum = db.IntegerProperty()
    ecoId = db.IntegerProperty()
    g200Region = db.StringProperty()
    g200Num = db.IntegerProperty()
    g200Biome = db.IntegerProperty()
    g200Stat = db.IntegerProperty()
    extentNorthWest = db.GeoPtProperty()
    extentSouthEast = db.GeoPtProperty()
    polyStrings = db.StringListProperty()
    dateCreated = db.DateTimeProperty(auto_now_add=True)
    
class TileSetIndex(db.Model):
    remoteLocation = db.LinkProperty() #remote url constructor for the dataset, for distributed storage
    zoom = db.IntegerProperty() #max zoom available for the layer
    proj = db.StringProperty() #max zoom available for the layer
    extentNorthWest = db.GeoPtProperty()
    extentSouthEast = db.GeoPtProperty()
    dateLastModified = db.DateTimeProperty()
    dateCreated = db.DateTimeProperty(auto_now_add=True)
    errors = db.StringListProperty()
    status = db.CategoryProperty()
    type = db.CategoryProperty()

class Tile(db.Model):
    band = db.BlobProperty()

class TileUpdate(db.Model):
    zoom = db.IntegerProperty()

class TmpTile(db.Model):
    band = db.TextProperty()

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
