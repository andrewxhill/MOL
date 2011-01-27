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
            worker_q.put({'jobtype': 'newraster', 'fullpath': fullpath})
            newitems.append(item)
        response.status = 202
        return 'Added new items to queue: %s ' % str(newitems)
        
    def index(self, format='html'):
        """GET /api: All items in the collection"""
        # url('api')

    def create(self):
        """POST /api: Create a new item"""
        # url('api')

    def new(self, format='html'):
        """GET /api/new: Form to create a new item"""
        # url('new_api')

    def update(self, id):
        """PUT /api/id: Update an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="PUT" />
        # Or using helpers:
        #    h.form(url('api', id=ID),
        #           method='put')
        # url('api', id=ID)

    def delete(self, id):
        """DELETE /api/id: Delete an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="DELETE" />
        # Or using helpers:
        #    h.form(url('api', id=ID),
        #           method='delete')
        # url('api', id=ID)

    def show(self, id, format='html'):
        """GET /api/id: Show a specific item"""
        # url('api', id=ID)

    def edit(self, id, format='html'):
        """GET /api/id/edit: Form to edit an existing item"""
        # url('edit_api', id=ID)
