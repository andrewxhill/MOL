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
from celery.task import Task, PeriodicTask
from celery.registry import tasks
from service import Layer, SpeciesIdError
from app_globals import Globals
from datetime import date, timedelta
import Queue
import logging
import os
import threading
import shutil


class BulkLoadTiles():
    """class for running the bulkloader to upload tilesets to GAE"""
    def __init__(self, id=None):
        self.id = id

    def uploadTiles(self):
        raise NotImplementedError()

class Test(Task):
    def run(self):
        a = 1
        b = 4
        logging.info(a+b)
        return a+b

class ScanNewLayers(Task):
    def run(self):
        """
        Scans the local filesystem for new shape files and adds them to the
        worker queue to process. Intended to be invoked by GAE.
        """     
        self.g = Globals()
        scan_dir = self.g.NEW_SHP_SCAN_DIR
        tmp_dir = self.g.TMP_SHP_SCAN_DIR
        logging.info(scan_dir)
        if not scan_dir:
            response.status = 404
            return
        for item in os.listdir(scan_dir):
            if os.path.splitext(item)[1] != '.shp':
                pass
                #full_path = os.path.join(scan_dir, item)
                #if not os.path.isdir(full_path):
                #    continue
            else:
                logging.info(item)
                shp_full_path = os.path.join(tmp_dir, item)
                logging.error(shp_full_path)
                for file in os.listdir(scan_dir):
                    if file.startswith(item.replace('.shp','')):
                        shutil.move(os.path.join(scan_dir, file), os.path.join(tmp_dir, file))    
                task = {self.g.Q_ITEM_JOB_TYPE: self.g.NEW_SHP_JOB_TYPE,
                    self.g.Q_ITEM_FULL_PATH: shp_full_path}
                LayerProcessingThread.apply_async(args=[self.g, task],countdown=480)
        return True
        
        
class LayerProcessingThread(Task):
    def run(self, g, task):
        """Tiles a shapefile specified in the task and registers metadata with
        GAE.

        Arguments:
            task - an item from the queue expected to have shapfile path
        """
        self.g = g
        logging.info(task)
        # Validates task:
        if task is None:
            logging.warn('newshp task was None')
            return
        if not task.has_key(self.g.Q_ITEM_FULL_PATH):
            logging.warn('newshp task does not have %s' % self.g.Q_ITEM_FULL_PATH)
            return
        fullpath = task[self.g.Q_ITEM_FULL_PATH]
        if fullpath is None or len(fullpath.strip()) == 0:
            logging.warn('newshp task has invalid path ' % fullpath)
            return

        logging.info('Starting new task')
        # Executes the job      
        layer = None
        # Sets the error log file:
        tail = os.path.split(fullpath)[1]
        root = os.path.splitext(tail)[0]
        errpath = os.path.join(self.g.ERR_DIR, '%s.log' % root)
        self.errlog = open(errpath, 'a+')
        
        try:
            layer = Layer(fullpath, self.g.TILE_DIR, self.g.ERR_DIR,
                          self.g.SRC_DIR, self.g.DST_DIR, self.g.MAP_XML,
                          self.g.TILE_URL,
                          self.g.LAYER_URL,
                          self.g.VALID_ID_SERVICE_URL,
                          zoom=self.g.TILE_MAX_ZOOM)                          
            logging.info('Layer created: ' + fullpath)
            layer.totiles(self.g)
            logging.info('Layers tiled in ' + self.g.TILE_DIR)
            logging.info('Layer metadata getting registered...')
            layer.register()
            logging.info('Layer getting cleaned up...')
            layer.cleanup()
            os.remove(errpath)

        
        except (SpeciesIdError), e:
            logging.info('SpeciesIdError ' + fullpath)
            self.errlog.write('SpeciesIdError ' + fullpath)
            id = Layer.idfrompath(fullpath)[0]
            logging.warn('id=' + id)
            err_dir = self.g.ERR_DIR
            src_dir = self.g.SRC_DIR
            err_dir = os.path.join(err_dir, 'animalia/species')
            # Copies to errors directory:
            for file in os.listdir(src_dir):
                if file.startswith(id):
                    shutil.copy2(os.path.join(src_dir, file), err_dir)
            # Removes from source directory:
            for file in os.listdir(src_dir):
                if file.startswith(id):
                    os.remove(os.path.join(src_dir, file))
                
        except (Exception), e:
            logging.error('Error while processing shapefile %s: %s' % (fullpath, str(e)))
            self.errlog.write('Error while processing shapefile %s: %s' % (fullpath, str(e)))
            if layer is not None:
                layer.cleanup(error=e)
            logging.error(str(e))
            # Ships error to App Engine:
            species_key_name = os.path.join('animalia/species',
                                            Layer.idfrompath(fullpath)[0])
            Layer.register_error(species_key_name, 'Exception', e.message,
                                 self.g.LAYER_URL)
            raise e

        # Notifies queue that this formerly enqueued task is complete:
        logging.info('Task complete')



class EcoregionProcessingThread(Task):
    def run(self, name, zoom, lowx, lowy, highx, highy, record_ids=None):
        self.g = Globals()
        
        url = "http://localhost/layers/api/ecoregion/tilearea/%s" % name
        vars = {"zoom": zoom,
                "lowx": lowx,
                "lowy": lowy,
                "highx": highx,
                "highy": highy}
        if record_ids is not None:
            vars["record_ids"] = record_ids
            
        logging.info('Task complete')

