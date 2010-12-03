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
  bDecode = {'+': '111110', '/': '111111', '1': '110101', '0': '110100', '3': '110111', '2': '110110', '5': '111001', '4': '111000', '7': '111011', '6': '111010', '9': '111101', '8': '111100', 'A': '000000', 'C': '000010', 'B': '000001', 'E': '000100', 'D': '000011', 'G': '000110', 'F': '000101', 'I': '001000', 'H': '000111', 'K': '001010', 'J': '001001', 'M': '001100', 'L': '001011', 'O': '001110', 'N': '001101', 'Q': '010000', 'P': '001111', 'S': '010010', 'R': '010001', 'U': '010100', 'T': '010011', 'W': '010110', 'V': '010101', 'Y': '011000', 'X': '010111', 'Z': '011001', 'a': '011010', 'c': '011100', 'b': '011011', 'e': '011110', 'd': '011101', 'g': '100000', 'f': '011111', 'i': '100010', 'h': '100001', 'k': '100100', 'j': '100011', 'm': '100110', 'l': '100101', 'o': '101000', 'n': '100111', 'q': '101010', 'p': '101001', 's': '101100', 'r': '101011', 'u': '101110', 't': '101101', 'w': '110000', 'v': '101111', 'y': '110010', 'x': '110001', 'z': '110011'}
  tile = Tiles(key_name=entity.key().name())
  tile.band = db.Blob(str(entity.band))
  yield op.db.Put(tile)   
