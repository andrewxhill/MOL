import logging
import math
import time
import os
import simplejson

from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.api import channel
from google.appengine.api import backends
from google.appengine.api import runtime
from google.appengine.api import taskqueue
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app


_MEMORY_LIMIT = 128  # The memory limit for a B1 server
_CULL_AMOUNT = 0.15


def _get_taskqueue_target():
    return '%d.%s' % (backends.get_instance(), backends.get_backend())


class CounterModel(db.Model):
    value = db.IntegerProperty(default=0)
    _dirty = False
    _last_accessed = None

    @classmethod
    def get_or_new(cls, name):
        model = cls.get_by_key_name(name)
        if model is None:
            model = cls(key_name=name)
        return model


class CounterStore(object):
    def __init__(self):
        self._store = {}
        self._has_shutdown = False
        self._dirty = False
        self._batch_size = 100

    def get_value(self, name):
        self._ensure_within_memory_limit()

        if name not in self._store:
            model = CounterModel.get_or_new(name)
            self._store[name] = model
        else:
            model = self._store[name]

        model._last_accessed = time.time()
        return model

    def inc_value(self, name, delta):
        if not self._dirty:
            # Enqueue a task with a 'target' specifying traffic be sent to this
            # instance of the backend.
            taskqueue.add(url='/backend/counter/flush',
                          target=_get_taskqueue_target(),
                          countdown=2)
            self._dirty = True

        model = self.get_value(name)
        model.value += delta
        model._dirty = True
        if self._has_shutdown:
            # Since the shutdown hook may be called at any time, we need to
            # protect ourselves against this.
            model.put()
        return model

    def _ensure_within_memory_limit(self):
        memory_limit = _MEMORY_LIMIT * 0.8

        memory_usage = runtime.memory_usage().current()
        if memory_usage >= memory_limit:
            # Create a list of candidate counters to remove. We remove counters
            # that have not been modified before those that have been modified,
            # then order them by the last time they were accessed.
            counters = self._store.values()
            counters.sort(key=lambda counter: (counter._dirty,
                                               counter._last_accessed))
            counters_to_cull = int(math.ceil(len(counters) * _CULL_AMOUNT))
            counters = counters[:counters_to_cull]

            logging.info('Removing %d entries as we are over the memory limit '
                         'by %dMB.',
                         counters_to_cull, memory_limit - memory_usage)

            self._write_in_batches(counters)
            for counter in counters:
                del self._store[counter.key().name()]

    def _put_counters(self, counters):
        db.put(counters)
        for counter in counters:
            counter._dirty = False

    def _write_in_batches(self, counters):
        """Write out the dirty entries from 'counters' in batches.

        The batch size is determined by self._batch_size.

        Args:
          counters: An iterable containing instances of CounterModel.
        """
        to_put = []
        for counter in counters:
            if counter._dirty:
                to_put.append(counter)

                if len(to_put) >= self._batch_size:
                    self._put_counters(to_put)
                    to_put = []

        if to_put:
            self._put_counters(to_put)

    def flush_to_datastore(self):
        """Write the dirty entries from _store to datastore."""
        self._write_in_batches(self._store.itervalues())
        self._dirty = False

    def shutdown_hook(self):
        """Ensures all counters are written to datastore."""
        if self._dirty:
            self.flush_to_datastore()
        self._has_shutdown = True



class HomeHandler(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
            return
        
class PageLoaded(webapp.RequestHandler):
    def post(self):
        logging.info('opened page')

class SearchHandler(webapp.RequestHandler):
  def post(self):
      user = users.get_current_user()
      if not user:
          self.redirect(users.create_login_url(self.request.uri))
          return      
      c = self.request.get('class', None)
      limit = self.request.get_range('limit', min_value=1, max_value=100, default=100)
      offset = self.request.get_range('offset', min_value=0, default=0)
      token = user.user_id()
      for i in range(20):
          offset = offset + limit
          channel.send_message(token, simplejson.dumps(
                  dict(
                      points=[[1,2],[3,4]],
                      limit=limit,
                      offset=offset)))


class HomeHandler(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
            return

        #c = self.request.get('class', None)
        limit = self.request.get_range('limit', min_value=1, max_value=100, default=100)
        offset = self.request.get_range('offset', min_value=0, default=0)
        
        token = channel.create_channel(user.user_id())
        template_values = {'token': token,
                           'limit': 100,
                           'offset': 0,
                          }
        self.response.out.write(template.render('index.html', template_values))        






class StartHandler(webapp.RequestHandler):
    """Handler for '/_ah/start'.

    This url is called once when the backend is started.
    """
    def get(self):
        runtime.set_shutdown_hook(_counter_store.shutdown_hook)


class FlushHandler(webapp.RequestHandler):
    """Handler for counter/flush.

    This handler is protected by login: admin in app.yaml.
    """
    def post(self):
        _counter_store.flush_to_datastore()

class CounterHandler(webapp.RequestHandler):
    """Handler for counter/{get,inc,dec}.

    This handler is protected by login: admin in app.yaml.
    """


    def _write_error(self, error_message):
        self.response.error(400)
        self.response.out.write(error_message)

    def post(self, method):
        """Handler a post to counter/{get,inc,dec}.

        The 'method' parameter is parsed from the url by a regex capture group.

        Args:
          method: The type of operation to perform against the counter store.
              It must be one of 'get', 'inc' or 'dec'.
        """
        key_name = self.request.get('name')
        delta = self.request.get('delta')

        if not key_name:
            self._write_error('Request did not have a "key_name" parameter.')
            return

        if method == 'get':
            model = _counter_store.get_value(key_name)
        else:
            if not delta:
                self._write_error('Request did not have a "delta" parameter.')
                return
            try:
                delta = int(delta)
            except ValueError:
                self._write_error('"delta" is not an integer.')
                return

            if method == 'inc':
                model = _counter_store.inc_value(key_name, delta)
            elif method == 'dec':
                model = _counter_store.inc_value(key_name, -delta)

        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write('%d' % model.value)


_handlers = [(r'/_ah/start', StartHandler),
             (r'/backend/points/home', HomeHandler),
             (r'/backend/points/search', SearchHandler),
             (r'/backend/points/opened', PageLoaded),
             (r'/backend/points/flush$', FlushHandler),
             (r'/backend/points/(get|inc|dec)$', CounterHandler)]

application = webapp.WSGIApplication(_handlers)
_counter_store = CounterStore()


def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
