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

# New workflow models

class Layer(model.Model):
    """Models a single layer from a source collection."""

    source = model.StringProperty('s', required=True)     # e.g., jetz
    collection = model.StringProperty('c', required=True) # e.g., mammals
    filename = model.StringProperty('f', required=True)   # e.g., puma_concolor
    json = model.TextProperty('j', required=True)         # e.g., all metadata as JSON

class LayerPolygon(model.Model): 
    """Models a Layer polygon (for use as a StructuredProperty of LayerIndex)."""

    # Required MoL DBF fields (http://goo.gl/UkzJW)
    #
    polygonid = model.StringProperty('p', required=True)
    areaid = model.StringProperty('a', required=True)
    specieslatin = model.StringProperty('s', required=True)
    source = model.StringProperty('r', required=True)

    # Optional MoL DBF fields (http://goo.gl/UkzJW) dynamically added during 
    # bulkloading.
    #
    # abundance
    # abundancecomment
    # abundancemakeup
    # abundancemethod
    # abundancesurveyarea
    # abundanceunits
    # dateend
    # datestart
    # distributioncomment
    # measurementcomment
    # measurementmethod
    # seasonality
    # bibliographiccitation
    # contributor
    # dynamicproperties
    # establishmentmeans
    # infraspecificepithet
    # occurrencestatus
    # population
    # scientificname
    # taxonid
    # taxonremarks
        
class LayerIndex(model.Model): # parent=Layer
    """Models a searchable model for Layer."""

    # Temporary DBF fields represented as JSON
    dbfjson = model.TextProperty('dbf', required=True)

    # All LayerPolygon entities for the Layer
    polygons = model.StructuredProperty(LayerPolygon, repeated=True)

    # Full text corpus
    corpus = model.StringProperty('c', repeated=True)
    
    # Required MOL metadata (http://goo.gl/98r46)
    #
    accessrights = model.StringProperty(required=True)
    bibliographiccitation = model.StringProperty(required=True)
    breedingdomain = model.StringProperty(required=True)
    contact = model.StringProperty(required=True)
    coverage = model.StringProperty(required=True)
    creator = model.StringProperty(required=True)
    date = model.StringProperty(required=True)
    description = model.StringProperty(required=True)
    email = model.StringProperty(required=True)
    eventdate = model.StringProperty(required=True)
    layertype = model.StringProperty(required=True)
    nonbreedingdomain = model.StringProperty(required=True)
    presencedefault = model.StringProperty(required=True)
    publisher = model.StringProperty(required=True)
    samplingprotocol = model.StringProperty(required=True)
    scientificname = model.StringProperty(required=True)
    source = model.StringProperty(required=True)
    subject = model.StringProperty(required=True)
    taxonomiccoverage = model.StringProperty(required=True)
    title = model.StringProperty(required=True)
    verbatimsrs = model.StringProperty(required=True)
    
    # Optional MoL metadata (http://goo.gl/98r46) dynamically added during 
    # bulkloading.
    #
    # accessright
    # basemaps: 
    # contributor
    # enddateaccuracy
    # format
    # identifier
    # language:
    # mapcount
    # maxregionsperspecies
    # maxx
    # maxy
    # medianregionsperspecies
    # minregionsperspecies
    # minx
    # miny
    # relation
    # rights
    # samplingprotocol
    # startdateaccuracy
    # taxonomy
    # type

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


    
