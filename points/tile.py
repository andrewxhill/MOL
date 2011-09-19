# Copyright 2011 Aaron Steele
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

__author__ = "Aaron Steele (eightysteele@gmail.com)"
__contributors__ = ["John Wieczorek (gtuco.btuco@gmail.com)"]

import cache
from model import PointIndex
import sources
import globalmaptiles as gmt
from ndb import query, model
from ndb.query import OR, AND
from sdl import interval
import png

from array import array
import logging
import simplejson
from StringIO import StringIO

from google.appengine.api import runtime
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

class PointTile(object):
    _blank_tile = None

    @classmethod
    def blank(cls):
        if not cls._blank_tile:
            tile = array('b', [1 for i in range(pow(256, 2))])
            f = StringIO()
            w = png.Writer(256, 256, greyscale=True, transparent=1)
            w.write_array(f, tile)
            cls._blank_tile = f.getvalue()
        return cls._blank_tile
        
    @classmethod
    def render(cls, pixels, n=5, dimension=256):
        # Create blank packed tile array
        tile = array('b', [1 for i in range(pow(dimension, 2))])

        # Render pixels
        for p in pixels:
            y, x = p
            
            # Calculate pixel bounds
            y0 = y - n
            x0 = x - n
            if y0 < 0:
                y0 = 0
            if x0 < 0:
                x0 = 0
            yn = y + n
            xn = x + n
            max_index = dimension - 1
            if yn > max_index:
                yn = max_index
            if xn > max_index:
                xn = max_index

            # Set pixel
            for y in range(y0, yn + 1):
                for x in range(x0, xn + 1):
                    tile[y * dimension + x] = 0

        return tile

class BoundingBoxSearch(object):
    
    @classmethod
    def range_query(cls, ranges, limit, offset, name=None, source_name=None):
        variables = []        
        qry = "PointIndex.query(AND(" 
        if name:
            qry = "%sPointIndex.name == '%s'," % (qry, name.strip().lower())
        if source_name:
            qry = "%sPointIndex.source == '%s'," % (qry, source_name.strip().lower())
            
        # Add range intervals to query
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
                logging.error('Unknown variable')
                return []
            intervals = interval.get_optimum_query_interval(var_min, var_max, gte, lt)
            if len(intervals) == 0:
                logging.info('No query possible')
                return []                
            qry = "%sOR(" % qry
            for index,value in intervals.iteritems():
                if not value or not index.startswith('i'):
                    continue
                index = index.replace('i', var)
                qry = '%sPointIndex.%s == %d,' % (qry, index, value)             
            if len(ranges) > 1:
                qry = '%s), ' % qry[:-1]
        
        # Complete query
        if len(ranges) > 1:
            qry = '%s)))' % qry[:-3]
        else:
            qry = '%s))) ' % qry[:-1]
        qry = eval(qry)
        #logging.info(qry)
        
        # Get query results
        results = [index.parent() for index in qry.fetch(limit, offset=offset, keys_only=True)]
        #if len(results) > 0:
        #    logging.info('Result count = %s' % len(results))
        return model.get_multi(results)

def get_tile_png(tx, ty, z, name, source_name, limit, offset):
    # Check cache for tile
    # key = '%s-%s-%s-%s-%s' % (tx, ty, z, name, source_name)
    # img = cache.get(key)
    # if img:
    #    return img
    # elif failfast:
    #    return None

    # Calculate Google tile bounding box
    mercator = gmt.GlobalMercator()
    s, w, n, e = mercator.GoogleTileLatLonBounds(tx, ty, z)

    # Create range for a bounding box query
    ranges = [('lat', s, n), ('lng', w, e)]

    # Construct tile pixels from points returned by a bounding box query
    pixels = set()        
    for point in BoundingBoxSearch.range_query(
        ranges, limit, offset, name=name, source_name=source_name):
        pixel_x, pixel_y = mercator.LatLngToRaster(point.lat, point.lng, z)
        pixel_x -= tx * 256
        pixel_y -= ty * 256
        pixels.add((pixel_y, pixel_x))

    if len(pixels) == 0:
        return None

    # Render the pixels in a new tile
    tile = PointTile.render(pixels)

    # Write the PNG tile image
    f = StringIO()
    w = png.Writer(256, 256, greyscale=True, transparent=1)
    w.write_array(f, tile)
    img = f.getvalue()
    # Cache and return the PNG tile image        
    # cache.add(key, img, dumps=False)
    return img

class TileService(webapp.RequestHandler):
    def get(self):
        self.post()

    def post(self):
        tx = self.request.get_range('x', None)
        ty = self.request.get_range('y', None)
        z = self.request.get_range('z', None)
        limit = self.request.get_range('limit', min_value=1, max_value=1000, default=1000)
        offset = self.request.get_range('offset', min_value=0, default=0)
        name = self.request.get('name', None)
        source_name = self.request.get('source', None)

        if tx is None or ty is None or z is None or name is None or source_name is None:
            self.error(400)
            return
        
        key = 'tile-%s-%s-%s-%s-%s' % (z, ty, tx, source_name, name)
        png = cache.get(key)
        if png is None:
            png = get_tile_png(tx, ty, z, name, source_name, limit, offset) 
            if png is None:
                png = PointTile.blank()
            cache.add(key, png, dumps=False)
    
        logging.info('TILE BACKEND MEMORY = %s' % runtime.memory_usage().current())
        self.response.set_status(200)
        self.response.headers['Content-Type'] = 'image/png'
        self.response.out.write(png)            

application = webapp.WSGIApplication([
     ('/backend/tile', TileService),
     ],
     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
