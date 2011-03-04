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
    """
    def scan(self):
        '''Scans the local filesystem for new shape files and adds them to the
        worker queue to process. Intended to be invoked by GAE.
        '''        
        scan_dir = app_globals.NEW_SHP_SCAN_DIR
        logging.info(scan_dir)
        if not scan_dir:
            response.status = 404
            return
        newitems = [] 
        layerCt = 0
        for item in os.listdir(scan_dir):
            if os.path.splitext(item)[1] != '.shp':
                pass
                #full_path = os.path.join(scan_dir, item)
                #if not os.path.isdir(full_path):
                #    continue
            else:
                logging.info(item)
                shp_full_path = os.path.join(scan_dir, item) #  '%s%s%s.shp' % (full_path, os.path.sep, item)
                if shp_full_path not in app_globals.QUEUED_LAYERS.keys() and layerCt < 5:
                    worker_q.put({app_globals.Q_ITEM_JOB_TYPE: app_globals.NEW_SHP_JOB_TYPE,
                                  app_globals.Q_ITEM_FULL_PATH: shp_full_path})
                    newitems.append(shp_full_path)
                    layerCt += 1
        response.status = 202
        return simplejson.dumps({'newitems':newitems, 'qsize':str(worker_q.qsize())})
    """
