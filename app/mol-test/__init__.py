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
from mol.db import Tile, TileUpdate, Species, SpeciesIndex, TileSetIndex
from mol.services import TileError, TileService, LayerService
import os
import time
import unittest

APP_ID = 'mol-lab'
AUTH_DOMAIN = 'gmail.com'
LOGGED_IN_USER = 'test@example.com'

class TileSetIndexTest(unittest.TestCase):
    
    def test_setters(self):
        obj = TileSetIndex()
        TileSetIndex.setzoom(obj, 1)
        self.assertEqual(obj.zoom, 1)
        
        obj.set_zoom(2)
        self.assertEqual(obj.zoom, 2)
        
class LayerServiceTest(unittest.TestCase):
    """Unit tests for LayerService class."""

    def setUp(self):
        """Sets up the test environment."""

        # The LayerService to use for testing:
        self.service = LayerService()

        # It's an error to register the same service twice:
        if apiproxy_stub_map.apiproxy.GetStub('datastore_v3') is not None:
            return;

        # Let's us run unit tests without running the dev server:
        os.environ['TZ'] = 'UTC'
        time.tzset()
        os.environ['SERVER_SOFTWARE'] = 'Development via nose'
        os.environ['SERVER_NAME'] = 'Foo'
        os.environ['SERVER_PORT'] = '8080'
        os.environ['APPLICATION_ID'] = APP_ID
        os.environ['USER_EMAIL'] = 'test@example.com'
        os.environ['CURRENT_VERSION_ID'] = 'testing-version'
        ds_stub = DatastoreFileStub(APP_ID, None, None)
        apiproxy_stub_map.apiproxy.RegisterStub('datastore_v3', ds_stub)

    def test_is_valid_id(self):
        self.assertEqual(False, self.service.is_id_valid(None))
        self.assertEqual(False, self.service.is_id_valid(''))
        self.assertEqual(False, self.service.is_id_valid(' '))
        self.assertEqual(False, self.service.is_id_valid('foo'))

        # Valid id
        key_name = 'testlayer'
        key = db.Key.from_path('Species', key_name)
        species = Species(key=key)
        id = str(db.put(species))
        self.assertEqual(True, self.service.is_id_valid(id))

        # Invalid id
        key_name = 'testlayerINVALID'
        key = db.Key.from_path('Species', key_name)
        id = str(key)
        self.assertEqual(False, self.service.is_id_valid(id))

        # Invalid id
        key_name = 'testlayer'
        key = db.Key.from_path('SpeciesIndex', key_name)
        species = SpeciesIndex(key=key)
        id = str(db.put(species))
        self.assertEqual(False, self.service.is_id_valid(id))

class TileServiceTest(unittest.TestCase):
    """Unit tests for TileService class."""

    def setUp(self):
        """Sets up the test environment."""

        # The TileService to use for testing:
        self.service = TileService()

        # It's an error to register the same service twice:
        if apiproxy_stub_map.apiproxy.GetStub('datastore_v3') is not None:
            return;

        # Let's us run unit tests without running the dev server:
        os.environ['TZ'] = 'UTC'
        time.tzset()
        os.environ['SERVER_SOFTWARE'] = 'Development via nose'
        os.environ['SERVER_NAME'] = 'Foo'
        os.environ['SERVER_PORT'] = '8080'
        os.environ['APPLICATION_ID'] = APP_ID
        os.environ['USER_EMAIL'] = 'test@example.com'
        os.environ['CURRENT_VERSION_ID'] = 'testing-version'
        ds_stub = DatastoreFileStub(APP_ID, None, None)
        apiproxy_stub_map.apiproxy.RegisterStub('datastore_v3', ds_stub)

    def test_put_tile(self):
        self.assertEqual(None, self.service.put_tile(None))
        self.assertEqual(None, self.service.put_tile(TileUpdate()))

        key_name = '00/021/pa'
        key = db.Key.from_path(TileService.TILE_KIND, key_name)
        tile = Tile(key=key)
        self.assertEqual(key, self.service.put_tile(tile))

    def test_put_tile_update(self):
        self.assertEqual(None, self.service.put_tile_update(None))
        self.assertEqual(None, self.service.put_tile_update(Tile()))

        # Test invalid zoom
        key_name = '00/xxx/pa'
        key = db.Key.from_path(TileService.TILE_KIND, key_name)
        tile = Tile(key=key)
        db.put(tile)
        tile_update_key = self.service.put_tile_update(tile)
        self.assertEqual(tile_update_key, None)

        # Test valid put
        key_name = '00/021/pa'
        key = db.Key.from_path(TileService.TILE_KIND, key_name)
        tile = Tile(key=key)
        db.put(tile)
        tile_update_key = self.service.put_tile_update(tile)
        self.assertNotEqual(tile_update_key, None)
        self.assertEqual(tile_update_key.name(), key_name)
        tile_update = db.get(tile_update_key)
        self.assertNotEqual(tile_update, None)
        self.assertEqual(tile_update.zoom, 3)


    def test_zoom_from_key(self):
        key_name = '00/021/pa'
        self.assertEqual(None, self.service._zoom_from_key_name(None))
        self.assertEqual(None, self.service._zoom_from_key_name('/'))
        self.assertEqual(None, self.service._zoom_from_key_name('//'))
        self.assertEqual(None, self.service._zoom_from_key_name('/x/y'))
        self.assertEqual('021', self.service._zoom_from_key_name('00/021/pa'))

    def test_is_tile(self):
        self.assertFalse(self.service._is_tile(None))
        self.assertFalse(self.service._is_tile(8))
        self.assertFalse(self.service._is_tile('Tile'))
        self.assertFalse(self.service._is_tile(TileUpdate()))
        self.assertTrue(self.service._is_tile(Tile()))

    def test_tile_from_url(self):
        # Tests valid urls:
        key_name = '00/021/pa'
        for url in [u'/api/entity/00/021/pa.png', u'/00/021/pa.png', u'00/021/pa']:
            entity = Tile(key=db.Key.from_path('Tile', key_name))
            data = '0101-%s' % url
            entity.band = db.Blob(str(data));
            entity.put()
            tile = self.service.tile_from_url(url)
            self.assertTrue(tile is not None)
            self.assertEqual(tile.key(), entity.key())
            self.assertEqual(tile.band, data)

        # Tests None:
        url = None
        tile = self.service.tile_from_url(url)
        self.assertEqual(tile, None)

        # Tests invalid urls:
        for url in ['', 'foo', '/api/tile/foo/bar/baz.png']:
            tile = self.service.tile_from_url(url)
            self.assertEqual(tile, None)


suite = unittest.TestLoader().loadTestsFromTestCase(TileSetIndexTest)
unittest.TextTestRunner(verbosity=2).run(suite)

#suite = unittest.TestLoader().loadTestsFromTestCase(LayerServiceTest)
#unittest.TextTestRunner(verbosity=2).run(suite)
#suite = unittest.TestLoader().loadTestsFromTestCase(TileServiceTest)
#unittest.TextTestRunner(verbosity=2).run(suite)
