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
from tempfile import NamedTemporaryFile
from layers.lib.mol.service import Layer, LayerError
import logging
import os
import shutil
import tempfile
import time
import unittest

EXAMPLE_SHAPEFILE_PATH = '/ftp/test/agdtb2wtbGFickELEgdTcGVjaWVzIjRhbmltYWxpYS9pbmZyYXNwZWNpZXMvYWJlbG9uYV9naWdsaW90b3NpX2d1YWxhcXVpemFlDA'
EXAMPLE_SHAPEFILE_ID = 'agdtb2wtbGFickELEgdTcGVjaWVzIjRhbmltYWxpYS9pbmZyYXNwZWNpZXMvYWJlbG9uYV9naWdsaW90b3NpX2d1YWxhcXVpemFlDA'

class LayerTest(unittest.TestCase):
    """Unit tests for Layer class."""
    
    def test_cleanup(self):
        # ----------------------------------------------------------------------
        # Cleanup without errors:
        
        # Sets up directories for testing:
        tiledir = tempfile.mkdtemp()
        errdir = tempfile.mkdtemp()
        newdir = tempfile.mkdtemp()
        archivedir = tempfile.mkdtemp()
        mapxml = '/ftp/tile/mapfile.xml'                
        shutil.copytree(EXAMPLE_SHAPEFILE_PATH, os.path.join(newdir, EXAMPLE_SHAPEFILE_ID)) 
        path = os.path.join(newdir, '%s/%s.shp' % (EXAMPLE_SHAPEFILE_ID, EXAMPLE_SHAPEFILE_ID))
        
        # Creates the layer
        layer = Layer(path, tiledir, errdir, newdir, archivedir, mapxml)
        self.assertNotEqual(layer, None)
        
        # Tiles and cleans up without errors:
        layer.totiles()
        layer.cleanup()        
        self.assertFalse(os.path.exists(os.path.join(newdir, EXAMPLE_SHAPEFILE_ID)))
        self.assertFalse(os.path.exists(os.path.join(errdir, EXAMPLE_SHAPEFILE_ID)))
        self.assertTrue(os.path.exists(os.path.join(archivedir, EXAMPLE_SHAPEFILE_ID)))
        self.assertTrue(os.path.exists(os.path.join(tiledir, EXAMPLE_SHAPEFILE_ID)))
        
        # Removes test directories:
        shutil.rmtree(tiledir)
        shutil.rmtree(errdir)
        shutil.rmtree(newdir)
        shutil.rmtree(archivedir)        

        # ----------------------------------------------------------------------
        # Cleanup with errors:
        
        tiledir = tempfile.mkdtemp()
        errdir = tempfile.mkdtemp()
        newdir = tempfile.mkdtemp()
        archivedir = tempfile.mkdtemp()
        mapxml = '/ftp/tile/mapfile.xml'                
        shutil.copytree(EXAMPLE_SHAPEFILE_PATH, os.path.join(newdir, EXAMPLE_SHAPEFILE_ID)) 
        path = os.path.join(newdir, '%s/%s.shp' % (EXAMPLE_SHAPEFILE_ID, EXAMPLE_SHAPEFILE_ID))
        
        # Creates the layer
        layer = Layer(path, tiledir, errdir, newdir, archivedir, mapxml)
        self.assertNotEqual(layer, None)
        
        # Tiles and cleans with errors:
        layer.totiles()
        layer.cleanup(error=True)        
        self.assertTrue(os.path.exists(os.path.join(newdir, EXAMPLE_SHAPEFILE_ID)))
        self.assertTrue(os.path.exists(os.path.join(errdir, EXAMPLE_SHAPEFILE_ID)))
        self.assertFalse(os.path.exists(os.path.join(archivedir, EXAMPLE_SHAPEFILE_ID)))
        self.assertFalse(os.path.exists(os.path.join(tiledir, EXAMPLE_SHAPEFILE_ID)))
        
        # Removes test directories:
        shutil.rmtree(tiledir)
        shutil.rmtree(errdir)
        shutil.rmtree(newdir)
        shutil.rmtree(archivedir)        

suite = unittest.TestLoader().loadTestsFromTestCase(LayerTest)
unittest.TextTestRunner(verbosity=2).run(suite)
