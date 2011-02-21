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
from layers.lib.mol.service import Layer, SpeciesIdError
import Queue
import logging
import os
import threading

worker_q = Queue.Queue()

class BulkLoadTiles():
    """class for running the bulkloader to upload tilesets to GAE"""
    def __init__(self, id=None):
        self.id = id

    def uploadTiles(self):
        raise NotImplementedError()

class LayerProcessingThread(threading.Thread):
    
    def __init__(self, g):
        threading.Thread.__init__(self)
        self.g = g
        
    def run(self):
        """Pulls tasks from the queue and dispatches based on job type."""
        ct = 0
        while True and ct < self.g.NEW_JOB_LIMIT:
            task = worker_q.get()
            jobtype = task[self.g.Q_ITEM_JOB_TYPE]
            logging.info('New job: ' + jobtype)
            if jobtype == self.g.NEW_SHP_JOB_TYPE:
                self.newshp(task)
            elif jobtype == self.g.BULKLOAD_TILES_JOB_TYPE:
                raise NotImplementedError()

    def newshp(self, task):
        """Tiles a shapefile specified in the task and registers metadata with
        GAE.

        Arguments:
            task - an item from the queue expected to have shapfile path
        """
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
        except (SpeciesIdError), e:
            # Invalid species ID
            pass # TODO
        except (Exception), e:
            logging.error('Error while processing shapefile %s: %s' % (fullpath, str(e)))
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
        worker_q.task_done()

def start_myworker(app_globals):
    worker = LayerProcessingThread(app_globals)
    worker.start()
