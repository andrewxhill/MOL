#!/usr/bin/env python
#
# Copyright 2011 Map Of Life
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
from layers.lib.base import BaseController
from layers.lib.taskqueue import worker_q
from layers.lib.mol.service import GenerateTiles
from pylons import response, request, app_globals
import logging
import os
import simplejson
from layers.lib.mol.service import Layer

log = logging.getLogger(__name__)

class ApiController(BaseController):
    
    def testid(self):
        id = request.params.get('id', None)
        url = request.params.get('url', None)
        return simplejson.dumps({'species_id':id, 'valid':Layer.isidvalid(id, url)})        
    
    def tiles(self, species_id, zoom, x, y):
        '''This action returns PNG data with the response header Content-Type 
        set to image/png with a 200 status code. It handles URLs of the form:
        
        http://mol.colorado.edu/tiles/species_id/zoom/x/y.png
        
        If a tile isn't found a 404 status is returned.
        '''
        png = os.path.join(app_globals.TILE_DIR, species_id, zoom, x, y + '.png')        
        if os.path.exists(png):
            logging.info('Returning tile : ' + png)
            response.headers['Content-Type'] = 'image/png'
            response.status = 200
            return open(png, 'rb').read()
        logging.info('Tile not found : ' + png)        
        response.status = 404
        
        
    def ecoregion(self, method, region_id, zoom):
        '''This action returns PNG data with the response header Content-Type 
        set to image/png with a 200 status code. It handles URLs of the form:
        
        http://mol.colorado.edu/ecoregion/region_id/zoom/x/y.png
        
        If a tile isn't found a 404 status is returned.
        '''
        if str(method).lower() == 'tile':
            x = request.GET['x']
            y = request.GET['y']
            png = os.path.join(app_globals.ECOTILE_DIR, region_id, zoom, x, y + '.png')        
            if os.path.exists(png):
                logging.info('Returning tile : ' + png)
                response.headers['Content-Type'] = 'image/png'
                response.status = 200
                return open(png, 'rb').read()
            logging.info('Tile not found : ' + png)        
            response.status = 404
            
        elif str(method).lower() == 'tilearea':
            '''This action returns PNG data with the response header Content-Type 
            set to image/png with a 200 status code. It handles URLs of the form:
            
            http://mol.colorado.edu/ecoregion/region_id/zoom/x/y.png
            
            If a tile isn't found a 404 status is returned.
            '''
            lowx = request.GET['lowx']
            lowy = request.GET['lowy']
            highx = request.GET['highx']
            highy = request.GET['highy']
            shp = os.path.join(app_globals.ECOSHP_DIR, region_id + '.shp')        
            if os.path.exists(shp):
                logging.info('Sending tiling job to queue : ' + shp)
                response.status = 200
                
                tmp_xml = open(app_globals.MAP_XML, 'r').read().replace('layer_name', region_id) 
                mapfile = os.path.join(app_globals.ECOSHP_DIR , region_id + '.mapfile.xml')
                logging.info('Creating mapfile: %s' + (mapfile))     
                open(mapfile, "w+").write(tmp_xml)
                
                bbox = (float(lowx), float(lowy), float(highx), float(highy))
                logging.info('Tiling %s found : %s' % (region_id,str(bbox)))      
                
                GenerateTiles.render_tiles(bbox,
                                           mapfile,
                                           app_globals.ECOTILE_DIR.rstrip('/') + "/",
                                           zoom,
                                           zoom+1,
                                           "MOL-ECOREGION",
                                           num_threads=app_globals.TILE_QUEUE_THREADS )
                                   
            logging.info('Region not found : ' + shp)        
            response.status = 404
