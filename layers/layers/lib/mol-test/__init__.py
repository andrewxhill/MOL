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
import os
import tempfile
import time
import unittest
from lib.mol.service import RasterLayer, RasterLayerError
from tempfile import NamedTemporaryFile

class LayerTest(unittest.TestCase):
    """Unit tests for LayerService class."""
      
    def test_constructor(self):
        valid = tempfile.mkdtemp()
        invalid = [None, '', ' ', '/#@$%#']        
        for dir in invalid:
            try:
                RasterLayer(dir, valid, valid, valid)
                self.fail("Invalid directory")
            except RasterLayerError as e:
                print e
        
        for dir in invalid:
            try:
                RasterLayer(valid, dir, valid, valid)
                self.fail("Invalid directory")
            except RasterLayerError as e:
                print e

        for dir in invalid:
            try:
                RasterLayer(valid, valid, dir, valid)
                self.fail("Invalid directory")
            except RasterLayerError as e:
                print e
                
        for dir in invalid:
            try:
                RasterLayer(valid, valid, valid, dir)
                self.fail("Invalid directory")
            except RasterLayerError as e:
                print e
            
        path = '/ftp/newraster/hbw00028'
        layer = RasterLayer(path, valid, valid, valid)
        self.assertNotEqual(None)
        
        
    def test_validatepath(self):
        pass
        # TODO
    
    def test_idfrompath(self):
        try:
            RasterLayer.idfrompath(None)
            self.fail('Invalid path')
            RasterLayer.idfrompath('')
            self.fail('Invalid path')
            RasterLayer.idfrompath(' ')
            self.fail('Invalid path')          
          
            # TODO: Checks for inaccessible paths
                    
        except RasterLayerError as e:
            print e
      
        f = NamedTemporaryFile(suffix='.txt')
        tail = os.path.split(f.name)[1]      
        root = os.path.splitext(tail)[0]
        self.assertEqual(root, RasterLayer.idfrompath(f.name))
      
suite = unittest.TestLoader().loadTestsFromTestCase(LayerTest)
unittest.TextTestRunner(verbosity=2).run(suite)
