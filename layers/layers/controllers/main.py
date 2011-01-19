import logging
import uuid

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to

from layers.lib.base import BaseController, render

from layers.lib.taskqueue import worker_q

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
        # Put the test file hbw00028 into the taskqueue
        #fullpath = '/ftp/newraster/hbw00028'
        fullpath = '/ftp/newraster/aghtb2wtYXBwc3ISCxIMVGlsZVNldEluZGV4GAEM'
        if worker_q.empty():
            worker_q.put({'id': 'aghtb2wtYXBwc3ISCxIMVGlsZVNldEluZGV4GAEM', 'jobtype': 'newraster', 'fullpath': fullpath})
            return 'In Queue'
        else:
            return 'Queue Full'
