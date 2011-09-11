import logging
import math
import time
import os
import simplejson
import urllib
from ndb import query, model
from ndb.query import OR, AND
from sdl import interval
import globalmaptiles as gmt

import png
from StringIO import StringIO

from google.appengine.api import memcache

from google.appengine.api import urlfetch
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

def handle_result(rpc, token, limit, offset):
    result = rpc.get_result()
    page = simplejson.loads(result.content)
    logging.info('PAGE %s' % page)
    points = [[x['decimallatitude'], x['decimallongitude']] for x in page]
    channel.send_message(token, simplejson.dumps(
            dict(
                points=points,
                limit=limit,
                offset=offset)))

def create_callback(rpc, token, limit, offset):
    return lambda: handle_result(rpc, token, limit, offset)

client_ids = {}

class DisconnectHandler(webapp.RequestHandler):
    def post(self):
        client_id = self.request.get('from')
        logging.info('Client %s disconnected' % client_id)
        client_ids[client_id] = False

class ConnectHandler(webapp.RequestHandler):
    def post(self):
        client_id = self.request.get('from')
        logging.info('Client %s connected' % client_id)
        client_ids[client_id] = True


class Point(model.Model):
    lat = model.FloatProperty('x', indexed=False)
    lng = model.FloatProperty('y', indexed=False)
    record = model.StringProperty('r', indexed=False)

class PointIndex(model.Model):
    lat = model.FloatProperty('y', indexed=False)
    lng = model.FloatProperty('x', indexed=False)
    source = model.StringProperty('s')
    genus = model.StringProperty('g')
    specificepithet = model.StringProperty('e')
    x0 = model.IntegerProperty()
    x1 = model.IntegerProperty()
    x2 = model.IntegerProperty()
    x3 = model.IntegerProperty()
    x4 = model.IntegerProperty()
    x5 = model.IntegerProperty()
    x6 = model.IntegerProperty()
    x7 = model.IntegerProperty()
    x8 = model.IntegerProperty()
    x9 = model.IntegerProperty()
    x10 = model.IntegerProperty()
    x11 = model.IntegerProperty()
    x12 = model.IntegerProperty()
    x13 = model.IntegerProperty()
    x14 = model.IntegerProperty()
    x15 = model.IntegerProperty()
    x16 = model.IntegerProperty()
    x17 = model.IntegerProperty()
    x18 = model.IntegerProperty()
    x19 = model.IntegerProperty()
    x20 = model.IntegerProperty()
    x21 = model.IntegerProperty()
    x22 = model.IntegerProperty()
    x23 = model.IntegerProperty()
    x24 = model.IntegerProperty()
    x25 = model.IntegerProperty()
    x26 = model.IntegerProperty()
    y0 = model.IntegerProperty()
    y1 = model.IntegerProperty()
    y2 = model.IntegerProperty()
    y3 = model.IntegerProperty()
    y4 = model.IntegerProperty()
    y5 = model.IntegerProperty()
    y6 = model.IntegerProperty()
    y7 = model.IntegerProperty()
    y8 = model.IntegerProperty()
    y9 = model.IntegerProperty()
    y10 = model.IntegerProperty()
    y11 = model.IntegerProperty()
    y12 = model.IntegerProperty()
    y13 = model.IntegerProperty()
    y14 = model.IntegerProperty()
    y15 = model.IntegerProperty()
    y16 = model.IntegerProperty()
    y17 = model.IntegerProperty()
    y18 = model.IntegerProperty()
    y19 = model.IntegerProperty()
    y20 = model.IntegerProperty()
    y21 = model.IntegerProperty()
    y22 = model.IntegerProperty()
    y23 = model.IntegerProperty()
    y24 = model.IntegerProperty()
    y25 = model.IntegerProperty()

    @classmethod
    def from_latlng(cls, lat, lng, genus, se, source):
        logging.info('lat=%s, lng=%s' % (lat, lng))
        lat = float(lat)
        lng = float(lng)
        pi = PointIndex(lng=lng, lat=lat, genus=genus, specificepithet=se, source=source)
        
        # Longitude (x)
        var_min = -180 * pow(10, 5)
        var_max =  180 * pow(10, 5)    
        varval = int(lng * pow(10, 5)) 
        intervals = interval.get_index_intervals(varval, var_min, var_max)
        for index,value in intervals.iteritems():
            model.IntegerProperty(name=index.replace('i', 'x'))._store_value(pi, value)
            #pi._properties[index.replace('i', 'x')] = value
            #pname = index.replace('i', 'x')
            #p = model.IntegerProperty(name=pname)
            #setattr(PointIndex, pname, p)
            #p._store_value(pi, value)

        # Latitude (y)
        var_min = -90 * pow(10, 5)
        var_max =  90 * pow(10, 5)
        varval = int(lat * pow(10, 5)) 
        intervals = interval.get_index_intervals(varval, var_min, var_max)
        for index,value in intervals.iteritems():
            model.IntegerProperty(name=index.replace('i', 'y'))._store_value(pi, value)
            #pi._properties[index.replace('i', 'y')] = value
            #pname = index.replace('i', 'y')
            #p = model.IntegerProperty(name=pname)
            #setattr(PointIndex, pname, p)
            #p._store_value(pi, value)

        pi._fix_up_properties()
        return pi

class PointTile(object):

    """Class representing a point tile."""

    @classmethod
    def blank(cls):
        """Returns a blank 256 x 256 tile."""
        return [256 * [1] for x in range(256)]
    
    @classmethod
    def bounds(cls, p, n):
        """Returns a 2-tuple (p0, pn) bounded within the tile."""
        p0 = p - n
        if p0 < 0:
            p0 = 0
        pn = p + n
        if pn > 255:
            pn = 255
        return p0, pn

    @classmethod    
    def render(cls, y, x, n, tile):
        """Renders a point in the tile with n-pixel neighbors rendered."""
        y0, yn = cls.bounds(y, n)
        x0, xn = cls.bounds(x, n)
        for y in range(y0, yn + 1):
            for x in range(x0, xn + 1):
                tile[y][x] = 0
        return tile
        
    @classmethod
    def create(cls, pixels, tx, ty, n=5):
        """Creates a point tile with pixels.
        
        pixels - sequence of y, x 2-tuples.
        ty - tile y
        tx - tile x
        
        """
        tile = cls.blank()
        for p in pixels:
            y, x = p
            tile = cls.render(y, x, n, tile)
        return tile
    
class TileHandler(webapp.RequestHandler):
    
    def get(self):
        tx = self.request.get_range('x')
        ty = self.request.get_range('y')
        z = self.request.get_range('z')
        limit = self.request.get_range('limit', min_value=1, max_value=100, default=10)
        offset = self.request.get_range('offset', min_value=0, default=0)
        genus = self.request.get('genus')
        source = self.request.get('source')

        # Check memcache for tile image hit
        mkey = '%s-%s-%s-%s' % (tx, ty, z, genus)
        img = memcache.get(mkey)
        if img:
            self.response.headers['Content-Type'] = 'image/png'
            self.response.out.write(img)
            return
        
        # Calculate Google tile bounding box
        mercator = gmt.GlobalMercator()
        s, w, n, e = mercator.GoogleTileLatLonBounds(tx, ty, z)
        
        # Create range for a bounding box query
        ranges = [('lat', s, n), ('lng', w, e)]
        
        # Construct tile pixels from points returned by a bounding box query
        pixels = set()        
        for point in BoundingBoxSearch.range_query(ranges, limit, offset, genus):
            pixel_x, pixel_y = mercator.LatLngToRaster(point.lat, point.lng, z)
            
            # TODO: Check these calcs for negative vals?
            pixel_x -= tx * 256
            pixel_y -= ty * 256

            pixels.add((pixel_y, pixel_x))
        logging.info('pixels=%s' % pixels)
        
        # Render the pixels in a new tile
        s = PointTile.create(pixels, tx, ty)
        
        # Write the PNG tile image
        f = StringIO()
        w = png.Writer(len(s[0]), len(s), greyscale=True, bitdepth=1, transparent=1)
        w.write(f, s)
        img = f.getvalue()

        # Cache and return the PNG tile image        
        memcache.add(mkey, img)
        self.response.headers['Content-Type'] = 'image/png'
        self.response.out.write(img)
        
class BoundingBoxSearch(webapp.RequestHandler):

    def get(self):
        ranges = [r.split(',') for r in self.request.get_all('r')]
        genus = self.request.get('genus', None)
        limit = self.request.get_range('limit', min_value=1, max_value=100, default=10)
        offset = self.request.get_range('offset', min_value=0, default=0)
        logging.info('ranges=%s' % ranges)
        self.range_query(ranges, limit, offset, genus)
    
    @classmethod
    def range_query(cls, ranges, limit, offset, genus): #gte, lt, var, limit, offset):
        variables = []

        # TODO: adapter interface for point sources (VertNet, GBIF)
        # TODO: Add filters for source and specificepithet
        if len(ranges) > 1:
            #qry = "PointIndex.query(AND(PointIndex.genus == '%s'," % genus
            qry = "PointIndex.query(AND(" 
        else:
            #qry = "PointIndex.query(AND(PointIndex.genus == '%s'," % genus
            qry = "PointIndex.query(AND(" 

        for r in ranges:
            var = r[0]
            variables.append(var)
            gte = int(float(r[1]) * pow(10, 5))
            lt = int(float(r[2]) * pow(10, 5))

            if var == 'lat':
                var = 'y'
                var_min = -90 * pow(10, 5)
                var_max =  90 * pow(10, 5)
            elif var == 'lng':
                var = 'x'
                var_min = -180 * pow(10, 5)
                var_max =  180 * pow(10, 5)
            else:
                #self.error(404)
                logging.error('Unknown variable')
                return []
            
            #var = WC_ALIAS.get(r[0])
            #logging.info('var=%s, gte=%s, lt=%s' % (var, gte, lt))
            intervals = interval.get_optimum_query_interval(var_min, var_max, gte, lt)
            #logging.info('intervals=%s, var=%s, gte=%s, lt=%s' % (len(intervals), var, gte, lt))
            #logging.info('Intervals: %s' % intervals)
            #logging.info('varmin: %s varmax: %s gte: %s lt: %s' %(var_min, var_max, gte, lt))

            if len(intervals) == 0:
                #self.error(404)
                logging.info('No query possible')
                return []
                
            # Build the query
            qry = "%sOR(" % qry
            #qry = "CellIndex.query(AND(CellIndex.n == '%s', OR(" % var
            for index,value in intervals.iteritems():
                if not value or not index.startswith('i'):
                    continue
                index = index.replace('i', var)
                #logging.info('index=%s, value=%s' % (index, value))
                qry = '%sPointIndex.%s == %d,' % (qry, index, value)
             
            if len(ranges) > 1:
                qry = '%s), ' % qry[:-1]
        
        if len(ranges) > 1:
            qry = '%s)))' % qry[:-3]
        else:
            qry = '%s))) ' % qry[:-1]
        #logging.info('qry=%s' % qry)
        qry = eval(qry)

        #logging.info(qry)
        results = qry.fetch(limit, offset=offset, keys_only=True)
        if len(results) > 0:
            logging.info('Result count = %s' % len(results))
        return model.get_multi(results)
        #cell_keys = set([key.parent().id() for key in results])


class SearchHandler(webapp.RequestHandler):

    # tasklet?
    def post(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
            return
        c = self.request.get('class', None)
        limit = self.request.get_range('limit', min_value=1, max_value=10, default=10)
        offset = self.request.get_range('offset', min_value=0, default=0)
        token = user.user_id()

        params = urllib.urlencode({'cl':'aves'})
        #url = 'http://localhost:8888/api/search?'
        url = 'http://eighty.vert-net.appspot.com/api/search?'
        while True:
            channel.send_message(token, url)
            response = simplejson.loads(urlfetch.fetch('%s%s' % (url, params)).content)
            model.put_multi([PointIndex.from_latlng(
                        r['decimallatitude'], 
                        r['decimallongitude'],
                        r.get('genus', None),
                        r.get('specificepithet', None),
                        'VertNet') for r in response['records']])
            offset = response['next_offset']
            params = urllib.urlencode({'cl':'aves', 'offset':offset})
            if not offset:
                break

        # for url in urls:

        #     result = urlfetch.fetch(url)
        #     page = simplejson.loads(result.content)
        #     #logging.info(url)
        #     points = [[x['decimallatitude'], x['decimallongitude']] for x in page]
        #     # results.append(simplejson.dumps(
        #     #         dict(
        #     #             points=points,
        #     #             limit=limit,
        #     #             offset=tmp_offset)))

        #     channel.send_message(token, simplejson.dumps(
        #             dict(
        #                 points=points,
        #                 limit=limit,
        #                 offset=tmp_offset)))
        #     tmp_offset = tmp_offset + limit







        # for x in results:
        #     logging.info('Sending result to client: %s bytes' % len(simplejson.dumps(x)))
        #     while not client_ids[token]:
        #         logging.info('Waiting for client to reconnect...')
        #     channel.send_message(token, x)

        # tmp_offset = offset
        # for url in urls:
        #     rpc = urlfetch.create_rpc()
        #     rpc.callback = create_callback(rpc, token, limit, tmp_offset)
        #     urlfetch.make_fetch_call(rpc, url)
        #     rpcs.append(rpc)
        #     tmp_offset = tmp_offset + limit

        # # Finish all RPCs, and let callbacks process the results.
        # for rpc in rpcs:
        #     rpc.wait()

        # for i in range(200):
        #     offset = offset + limit
        #     channel.send_message(token, simplejson.dumps(
        #             dict(
        #                 points=[[1,2],[3,4]],
        #                 limit=limit,
        #                 offset=offset)))


class HomeHandler(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
            return

        #c = self.request.get('class', None)
        limit = self.request.get_range('limit', min_value=1, max_value=100, default=100)
        offset = self.request.get_range('offset', min_value=0, default=0)

        #token = channel.create_channel(user.user_id())
        logging.info('Opening channel with client id %s' % token)
        client_ids[user.user_id()] = True
        template_values = {'token': 'hi',
                           'limit': 10,
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
             (r'/_ah/channel/disconnected/', DisconnectHandler),
             (r'/_ah/channel/connected/', ConnectHandler),
             (r'/backend/points/home', HomeHandler),
             (r'/backend/points/search', SearchHandler),
             (r'/backend/points/tile', TileHandler),
             (r'/backend/points/bb', BoundingBoxSearch),
             (r'/backend/points/opened', PageLoaded),
             (r'/backend/points/flush$', FlushHandler),
             (r'/backend/points/(get|inc|dec)$', CounterHandler)]

application = webapp.WSGIApplication(_handlers)
_counter_store = CounterStore()


def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
