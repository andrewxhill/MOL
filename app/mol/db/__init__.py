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

class Tile(db.Model):
  band = db.BlobProperty()
  def put(self):
    memcache.set("tile-%s" % self.key().name(), self.band, 180)
    tmpK = self.key().name().split('/')
    tmpK[1] = tmpK[1][0:-1]
    zoom = len(tmpK[1])
    tmpK = '/'.join(tmpK)
    if zoom > 0:
        tmp = TileUpdate(key=db.Key.from_path('TileUpdate',tmpK))
        tmp.zoom = zoom
        tmp.put()
    return db.Model.put(self)

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
  kingdom = db.StringProperty()
  phylum = db.StringProperty()
  class_ = db.StringProperty()
  order_ = db.StringProperty()
  superFamily = db.StringProperty()
  family = db.StringProperty()
  genus = db.StringProperty()
  species = db.StringProperty()
  infraSpecies = db.StringProperty()
   

