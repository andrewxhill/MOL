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
from mol.db import Tiles
from mol.services import TileError, TileService
import os
import time
import unittest

APP_ID = 'mol-lab' 
AUTH_DOMAIN = 'gmail.com' 
LOGGED_IN_USER = 'test@example.com' 

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

  def test_tile_from_request_path(self):
    # Tests valid paths:
    key_name = '00/021/pa'
    for path in [u'/api/entity/00/021/pa.png', u'/00/021/pa.png', u'00/021/pa']:
      entity = Tiles(key=db.Key.from_path('Tiles', key_name))
      data = '0101-%s' % path
      entity.band = db.Blob(str(data));
      entity.put()      
      tile = self.service.tile_from_request_path(path)
      self.assertTrue(tile is not None)
      self.assertEqual(tile.key(), entity.key())
      self.assertEqual(tile.band, data)
      
    # Tests None:
    path = None
    tile = self.service.tile_from_request_path(path)
    self.assertEqual(tile, None)
    
    # Tests invalid paths:
    for path in ['', 'foo', '/api/tile/foo/bar/baz.png']:
      try :
        tile = self.service.tile_from_request_path(path)
        self.fail('Invalid path %s should cause failure' % path)
      except TileError as error:
        print error
            
  def test_tile_key_from_request_path(self):
    # Tests valid paths:
    key_name = '00/021/pa'
    for path in [u'/api/entity/00/021/pa.png', u'/00/021/pa.png', u'00/021/pa']:
      entity = Tiles(key=db.Key.from_path('Tiles', key_name))
      entity.band = db.Blob(str('0101'));
      entity.put()      
      key = self.service.tile_key_from_request_path(path)
      self.assertTrue(key is not None)
      self.assertEqual(key, entity.key())

    # Tests None:
    path = None
    key = self.service.tile_key_from_request_path(path)
    self.assertEqual(key, None)
    
    # Tests invalid paths:
    for path in ['', 'foo', '/api/tile/foo/bar/baz.png']:
      try :
        key = self.service.tile_key_from_request_path(path)
        self.fail('Invalid path %s should cause failure' % path)
      except TileError as error:
        print error
      
  def test_is_valid_request_path(self):
    # Tests valid paths:
    for path in ['/api/entity/00/021/pa.png', '/00/021/pa.png', '00/021/pa']:
      self.assertTrue(self.service.is_valid_request_path(path))

    # Tests invalid paths:
    for path in ['', None, 'foo', '/api/tile/foo/bar/baz.png']:
      self.assertFalse(self.service.is_valid_request_path(path))

suite = unittest.TestLoader().loadTestsFromTestCase(TileServiceTest)
unittest.TextTestRunner(verbosity=2).run(suite)