from layers.lib.base import BaseController, render
from pylons import config, request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
import logging
import os
from layers.lib.taskqueue import worker_q

log = logging.getLogger(__name__)

class ApiController(BaseController):

    def scan(self):
        scan_dir = config['pylons.app_globals'].NEW_RASTER_SCAN_DIR
        if not scan_dir:
            response.status = 404
            return

        newitems = []        
        for item in os.listdir(scan_dir):
            print item
            ext = os.path.splitext(item)[1]
            if ext != '.shp':
                continue
            fullpath = os.path.join(scan_dir, item)
            worker_q.put({'jobtype': 'newshape', 'fullpath': fullpath})
            newitems.append(item)
        response.status = 202
        return 'Added new items to queue: %s ' % str(newitems)
        
