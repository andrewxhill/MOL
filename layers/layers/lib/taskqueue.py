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
import Queue
import logging
import threading
from layers.lib.mol.service import Layer

TILE_DIR = "/ftp/tile/"
ERR_DIR = "/ftp/error/"
SRC_DIR = "/ftp/new/"
DST_DIR = "/ftp/archive/"
MAP_XML = "/ftp/tile/mapfile.xml"

NEW_RASTER_JOB_TYPE = 'newraster'
NEW_SHP_JOB_TYPE = 'newshp'
BULKLOAD_TILES_JOB_TYPE = 'bulkload-tiles'
Q_ITEM_FULL_PATH = 'fullpath'
Q_ITEM_JOB_TYPE = 'jobtype'

worker_q = Queue.Queue()

class BulkLoadTiles():
    """class for running the bulkloader to upload tilesets to GAE"""
    def __init__(self, id=None):
        self.id = id

    def uploadTiles(self):
        raise NotImplementedError()

class LayerProcessingThread(threading.Thread):

    def run(self):
        """Pulls tasks from the queue and dispatches based on job type."""
        while True:
            task = worker_q.get()
            jobtype = task[Q_ITEM_JOB_TYPE]
            logging.info('New job: ' + jobtype)
            if jobtype == NEW_SHP_JOB_TYPE:
                self.newshp(task)
            elif jobtype == BULKLOAD_TILES_JOB_TYPE:
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
        if not task.has_key(Q_ITEM_FULL_PATH):
            logging.warn('newshp task does not have %s' % Q_ITEM_FULL_PATH)
            return
        fullpath = task[Q_ITEM_FULL_PATH]
        if fullpath is None or len(fullpath.strip()) == 0:
            logging.warn('newshp task has invalid path ' % fullpath)
            return

        logging.info('Starting new task')
        # Executes the job      
        layer = None
        try:
            layer = Layer(fullpath, TILE_DIR, ERR_DIR, SRC_DIR, DST_DIR, MAP_XML)
            logging.info('Layer created: ' + fullpath)
            layer.totiles()
            logging.info('Layers tiled in ' + TILE_DIR)
            logging.info('Layer metadata getting registered...')
            layer.register()
            logging.info('Layer getting cleaned up...')
            layer.cleanup()
        except (Exception), e:
            logging.error('Error while processing shapefile %s: %s' % (fullpath, str(e)))
            if layer is not None:
                layer.cleanup(error=e)
            logging.error(str(e))
            # Ships error to App Engine:
            Layer.register_error(Layer.idfrompath(fullpath)[0], 'Exception', e.message)
            raise e

        # Notifies queue that this formerly enqueued task is complete:
        logging.info('Task complete')
        worker_q.task_done()

def start_myworker():
    worker = LayerProcessingThread()
    worker.start()
