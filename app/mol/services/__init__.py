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

from abc import ABCMeta, abstractmethod, abstractproperty
from google.appengine.api import apiproxy_stub, apiproxy_stub_map
from google.appengine.api.datastore_file_stub import DatastoreFileStub
from google.appengine.ext import db
from math import ceil
from mol.db import Tiles
import cStringIO
import os
import png
import re

class Error(Exception):
  """Base class for exceptions in this module."""
  pass
  
class TileError(Error):
  """Exception raised for errors related to Tiles.

  Attributes:
    expr -- input expression in which the error occurred
    msg  -- explanation of the error
  """

  def __init__(self, expr, msg):
    self.expr = expr
    self.msg = msg

class AbstractTileService(object):
  """An abstract base class for working with Tile entities."""
  
  __metaclass__ = ABCMeta
  
  def tile_from_request_path(self, path):
    """Returns the Tile associated with a entity URL request path.
    
    Args:
      path: The entity URL request path (e.g., /api/entity/00/021/pa.png)

    Returns:
      The Tile associated with the path or None if it does not exist.        
    """
    raise NotImplementedError()
  
  def tile_key_from_request_path(self, path):
    """Returns the Tile key associated with a entity URL request path.
    
    Args:
      path: The entity URL request path (e.g., /api/entity/00/021/pa.png)

    Returns:
      The Tile key associated with the path or None if it does not exist.
    """
    raise NotImplementedError()
  
  def is_valid_request_path(self, path):
    """State checking method that returns true if the request path is valid.
    
    This method is useful when clients do not want to deal with catching a 
    TileError exception when parsing an invalid request path.
    
    Args:
      path: The entity URL request path (e.g., /api/entity/00/021/pa.png)

    Returns:
      True if the path is valid and False otherwise.
    """
    raise NotImplementedError()
  
class TileService(AbstractTileService):
  
  KEY_NAME_PATTERN = '[\d]+/[\d]+/[\w]+'
  ENTITY_KIND = "Tiles"
  
  def tile_key_from_request_path(self, path):
    if path is None:
      return None
    try:
      key_name = re.findall(self.KEY_NAME_PATTERN, path)[0]
      key = db.Key.from_path(self.ENTITY_KIND, key_name)
      return key
    except IndexError as error:
      raise TileError(error, 'Invalid path %s' % path)
      
  def tile_from_request_path(self, path):
    if path is None:
      return None
    key = self.tile_key_from_request_path(path)
    entity = Tiles.get(key)
    return entity
  
  def is_valid_request_path(self, path):
    if path is None:
      return False
    try:
      self.tile_key_from_request_path(path)
      return True
    except TileError:
      return False