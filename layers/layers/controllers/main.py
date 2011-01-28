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
from layers.lib.base import BaseController, BaseController, render
from layers.lib.taskqueue import worker_q, NEW_SHP_JOB_TYPE, worker_q, \
    NEW_SHP_JOB_TYPE, start_myworker
from pylons import config, config, request, response, session, tmpl_context as c, \
    url
from pylons.controllers.util import abort, redirect
import logging
import logging
import os
import uuid


log = logging.getLogger(__name__)

def layer_processing_ids():
    return uuid.uuid4()

class MainController(BaseController):

    def index(self):
        # Return a rendered template
        #return render('/main.mako')
        # or, return a response
        return 'Hello World'
    
    def test_task(self):
        id = 'agdtb2wtbGFickELEgdTcGVjaWVzIjRhbmltYWxpYS9pbmZyYXNwZWNpZXMvYWJlbG9uYV9naWdsaW90b3NpX2d1YWxhcXVpemFlDA'
        fullpath = '/ftp/example/%s/%s.shp' % (id, id)
        logging.info(fullpath)
        if worker_q.empty():
            worker_q.put({'id': id, 'jobtype': NEW_SHP_JOB_TYPE, 'fullpath': fullpath})
            return 'In Queue'
        else:
            return 'Queue Full'
