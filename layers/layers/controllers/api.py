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
from layers.lib.base import BaseController, render
from layers.lib.taskqueue import worker_q, NEW_SHP_JOB_TYPE, Q_ITEM_FULL_PATH, Q_ITEM_JOB_TYPE, start_myworker
from pylons import config, request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
import logging
import os
import simplejson

log = logging.getLogger(__name__)

class ApiController(BaseController):

    def scan(self):
        '''Scans the remote server for new shape files and adds them to the
        worker queue to process. Intended to be invoked by GAE.
        '''        
        scan_dir = config['pylons.app_globals'].NEW_SHP_SCAN_DIR
        logging.info(scan_dir)
        if not scan_dir:
            response.status = 404
            return
        newitems = []        
        for item in os.listdir(scan_dir):
            full_path = os.path.join(scan_dir, item)
            if not os.path.isdir(full_path):
                continue
            shp_full_path = '%s%s%s.shp' % (full_path, os.path.sep, item)
            worker_q.put({Q_ITEM_JOB_TYPE: NEW_SHP_JOB_TYPE,
                          Q_ITEM_FULL_PATH: shp_full_path})
            newitems.append(shp_full_path)
        response.status = 202
        return simplejson.dumps({'newitems':newitems})
          
