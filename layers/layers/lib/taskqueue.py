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
from mol.service import GenerateTiles, Layer, LayerError
import Queue
import logging
import threading

TILE_DIR = "/ftp/tiles/"
ASC_DIR = "/ftp/asc/"
ERR_DIR = "/ftp/errors/"
SRC_DIR = "/ftp/newraster/"
DST_DIR = "/ftp/grid/"
SHP_DIR = "/ftp/shp/"
MAP_XML = "/ftp/mapfile.xml"

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
        """Tiles an asc file speicified in the task and registers metadata with
        GAE.

        Arguments:
            task - an item from the queue expected to have acs path
        """
        # Validates task:
        if task is None:
            # TODO
            return
        if not task.has_key(Q_ITEM_FULL_PATH):
            # TODO
            return
        fullpath = task[Q_ITEM_FULL_PATH]
        if fullpath is None or len(fullpath.strip()) == 0:
            # TODO
            return

        # Executes the job      
        layer = Layer(fullpath, TILE_DIR, ASC_DIR, ERR_DIR, SRC_DIR, DST_DIR, MAP_XML)
        try:

            layer.totiles()
            layer.register()
            layer.cleanup()
        except LayerError as e:
            # TODO
            print 'LayerError: ' + e.msg
        except Exception as e:
            # TODO
            print 'Exception: ' + str(e)

        # Notifies queue that this formerly enqueued task is complete:
        worker_q.task_done()

def start_myworker():
    worker = LayerProcessingThread()
    worker.start()
