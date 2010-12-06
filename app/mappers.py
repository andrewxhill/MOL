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

from mapreduce import operation as op
from google.appengine.ext import db
from Tiles import Tiles, TmpTiles, TileUpdates

def delete(entity):
  """Deletes the entity from the datastore."""
  if len(entity.key().name().split('/')[1]) < 6:
    yield op.db.Delete(entity)
  

def tile(entity):
  """Converts a TmpTiles entity into a Tiles entity.

  Basically we convert the TmpTiles entity to a Tiles entity by using the same
  key name and then converting the Text band in TmpTiles to a Blob band in Tiles.
  Since a Blob requires a str argument, the Text band is converted to str.

  Args:
      entity: A TmpTiles entity
  """
  """
  queue = TileUpdates(key_name=entity.key().name())
  yield op.db.Put(queue)
  """
  tile = Tiles(key_name=entity.key().name())
  tile.band = db.Blob(str(entity.band))
  yield op.db.Put(tile)   
   
