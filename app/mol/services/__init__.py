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
from google.appengine.api import apiproxy_stub, apiproxy_stub_map
from google.appengine.api.datastore_file_stub import DatastoreFileStub
from google.appengine.ext import db
from math import ceil
from mol.db import Tile, TileUpdate, TileSetIndex
import cStringIO
import os
import png
import re
from google.appengine.api.datastore_errors import BadKeyError

class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class TileError(Error):
    """Exception raised for errors related to Tile.

    Attributes:
      expr -- input expression in which the error occurred
      msg  -- explanation of the error
    """

    def __init__(self, expr, msg):
        self.expr = expr
        self.msg = msg

class AbstractLayerService(object):
    """An abstract base class for the Layer service."""

    def is_id_valid(self, id):
        """Returns true if the id is valid, otherwise returns false."""
        raise NotImplementedError()

class LayerService(AbstractLayerService):

    def is_id_valid(self, id):
        # Checks input for null or empty string:
        if id is None:
            return False
        if len(id.strip()) == 0:
            return False

        # Checks if the id can be encoded into a Key:
        key = None
        try:
            key = db.Key(id)
            if key is None:
                return False
        except BadKeyError:
            return False

        # Checks for a Species kind with an entity in the datastore:
        if key.kind() != 'Species':
            return False
        if db.get(key) is None:
            return False

        # Passed all checks so id is valid:
        return True

class AbstractTileService(object):
    """An abstract base class for the Tile service."""

    def put_tile(self, tile):
        """Puts a Tile in the datastore. Returns a key or None if it wasn't put."""
        raise NotImplementedError()

    def put_tile_update(self, tile):
        """Puts a TileUpdate for a Tile in the datastore. Returns a key or None if
        it wasn't put.
        """
        raise NotImplementedError()

    def tile_from_url(self, url):
        """Returns the Tile associated with a entity URL request url or None if a
        Tile could not be found."""
        raise NotImplementedError()

class TileService(AbstractTileService):

    KEY_NAME_PATTERN = '[\d]+/[\d]+/[\w]+'
    TILE_KIND = 'Tile'
    TILE_UPDATE_KIND = 'TileUpdate'

    @staticmethod
    def _is_tile(tile):
        return tile is not None and isinstance(tile, Tile)

    @staticmethod
    def _zoom_from_key_name(key_name):
        if key_name is None:
            return None
        if key_name.count('/') < 2:
            return None
        zoom = key_name.split('/')[1]
        try:
            int(zoom)
        except ValueError:
            return None
        return zoom

    def put_tile(self, tile, update=True):
        if not TileService._is_tile(tile):
            return None
        key = db.put(tile)
        if update:
            self.put_tile_update(tile)
        return key

    def put_tile_update(self, tile):
        if not TileService._is_tile(tile):
            return None
        if not tile.is_saved() or tile.key().name() is None:
            return None
        key_name = tile.key().name()
        zoom = self._zoom_from_key_name(key_name)
        if zoom is None:
            return None
        tu_key = db.Key.from_path(self.TILE_UPDATE_KIND, key_name)
        tu = TileUpdate(key=tu_key)
        tu.zoom = len(zoom)
        tu_key = db.put(tu)
        return tu_key

    def tile_from_url(self, url):
        if url is None:
            return None
        key = self._key_name(url)
        if key is None:
            return None
        entity = Tile.get(key)
        return entity

    def _key_name(self, string):
        if string is None:
            return None
        try:
            key_name = re.findall(self.KEY_NAME_PATTERN, string)[0]
            key = db.Key.from_path(self.TILE_KIND, key_name)
            return key
        except IndexError:
            return None
