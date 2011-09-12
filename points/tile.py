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
import sources
from model import PointIndex
import globalmaptiles as gmt
from ndb import query, model
from ndb.query import OR, AND
from sdl import interval
import png
from StringIO import StringIO

import logging
import simplejson

from google.appengine.api import backends
from google.appengine.api import taskqueue
from google.appengine.api import urlfetch
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

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
        
        pixels - sequence of (y,x) 2-tuples.
        ty - tile y
        tx - tile x
        
        """
        tile = cls.blank()
        for p in pixels:
            y, x = p
            tile = cls.render(y, x, n, tile)
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
        results = qry.fetch(limit, offset=offset, keys_only=True)
        #if len(results) > 0:
        #    logging.info('Result count = %s' % len(results))
        return model.get_multi(results)

def get_tile_png(tx, ty, z, name, source_name, limit, offset, failfast=False):
    # Check cache for tile
    key = '%s-%s-%s-%s-%s' % (tx, ty, z, name, source_name)
    img = cache.get(key)
    if img:
        return img
    
    if failfast:
        return None

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

    # Render the pixels in a new tile
    s = PointTile.create(pixels, tx, ty)

    # Write the PNG tile image
    f = StringIO()
    w = png.Writer(len(s[0]), len(s), greyscale=True, bitdepth=1, transparent=1)
    w.write(f, s)
    img = f.getvalue()

    # Cache and return the PNG tile image        
    cache.add(key, img, dumps=False)
    return img

class TileService(webapp.RequestHandler):
    def get(self):
        tx = self.request.get_range('x')
        ty = self.request.get_range('y')
        z = self.request.get_range('z')
        limit = self.request.get_range('limit', min_value=1, max_value=1000, default=1000)
        offset = self.request.get_range('offset', min_value=0, default=0)
        name = self.request.get('name')
        source_name = self.request.get('source')
        
        # Backend task for pre-rendering tiles at next 2 zoom levels
        params = dict(name=name, source=source_name, minzoom=z+1, maxzoom=z+2)
        taskqueue.add(url='/backend/render', target='render', params=params)

        # Render and return tile for this request
        tile_png = get_tile_png(tx, ty, z, name, source_name, limit, offset)
        self.response.headers['Content-Type'] = 'image/png'
        self.response.out.write(tile_png)

application = webapp.WSGIApplication([
     ('/backend/tile', TileService),
     ],
     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
