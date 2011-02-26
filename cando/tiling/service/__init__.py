#
# Copyright 2010 Map Of Life
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
from osgeo import gdal, ogr
from urllib2 import HTTPError
import GenerateTiles
import datetime
import logging
import math
import os.path
import shutil
import simplejson
import subprocess
import urllib
import urllib2

class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class SpeciesIdError(Error):
    pass

class LayerError(Error):
    """Exception raised for errors related to raster layers.

    Attributes:
      expr -- input expression in which the error occurred
      msg  -- explanation of the error
    """

    def __init__(self, expr, msg):
        self.expr = expr
        self.msg = msg

    def __str__(self):
        return self.msg

def _isempty(s):
    return len(s.strip()) == 0

class _RequestWrapper(urllib2.Request):
    '''Wraps urllib2.Request so that it supports PUT and DELETE.'''
    def __init__(self, method, *args, **kwargs):
        self._method = method
        urllib2.Request.__init__(self, *args, **kwargs)

    def get_method(self):
        if self._method:
            return self._method
        elif self.has_data():
            return 'POST'
        else:
            return 'GET'

class _PutRequest(_RequestWrapper):
    '''Helper class for PUT requests.'''
    def __init__(self, *args, **kwargs):
        _RequestWrapper.__init__(self, 'PUT', *args, **kwargs)
                
def MetersToLatLon(bb):
    "Spherical Mercator EPSG:900913 to lat/lon in WGS84 Datum"        
    sh = 2 * math.pi * 6378137 / 2.0
    mx, mx0, my, my0 = bb[0], bb[1], bb[2], bb[3]
    lon = (mx / sh) * 180.0
    lon0 = (mx0 / sh) * 180.0
    lat = (my / sh) * 180.0
    lat0 = (my0 / sh) * 180.0
    lat = 180 / math.pi * (2 * math.atan(math.exp(lat * math.pi / 180.0)) - math.pi / 2.0)
    lat0 = 180 / math.pi * (2 * math.atan(math.exp(lat0 * math.pi / 180.0)) - math.pi / 2.0)
    return lon, lat, lon0, lat0
    
    
class _GdalUtil(object):
    """GDAL Utility class with static helper methods."""

    @staticmethod
    def getboundingbox(geotrans):
        """Returns a bounding box coordinate dictionary with maxLat, minLat,
        maxLon, and minLon keys given the affine transformation coefficients
        returned from osgeo.gdal.Dataset.GetGeoTransform().

        Arguments:
            geotrans - the affine transformation coefficients tuple.

        Returns:
            Dictionary with maxLat, minLat, maxLon, and minLon keys.
        """
        return {'maxLat': max(list(geotrans)[1::2]),
                'minLat': min(list(geotrans)[1::2]),
                'maxLon': max(list(geotrans)[0::2]),
                'minLon': min(list(geotrans)[0::2])
                }

    @staticmethod
    def getmetadata(filepath):
        """Returns a metadata dictionary for the asc file identified by filepath
        with the following keys:

        proj - The projection
        bb - The bounding box coordinates

        Arguments:
            filepath - path to an asc file

        Returns:
            Dictionary with proj and bb keys or None if error.

        Raises:
            LayerError if filepath is invalid.
        """
        Layer.validatepath(filepath, dir=False)
        vector = ogr.GetDriverByName('ESRI Shapefile')
        src_ds = vector.Open(filepath)
        src_lyr = src_ds.GetLayer(0)
        src_extent = src_lyr.GetExtent()
        bb = MetersToLatLon(src_extent)
        bb = {'minLon': bb[0], 'minLat': bb[1], 'maxLon': bb[2], 'maxLat': bb[3]}
        """
        ascdata = gdal.Open(filepath)
        if ascdata is None:
            return None
        projection = ascdata.GetProjection()
        geotrans = ascdata.GetGeoTransform()
        bb = _GdalUtil.getboundingbox(geotrans)
        """
        return {'proj' : 'EPSG:900913', 'geog': bb}, src_extent

class Layer(object):

    @staticmethod
    def register_error(species_key_name, kind, msg, layerurl):
        '''Registers an error with App Engine.'''
        params = {'errors': simplejson.dumps({'kind':kind, 'message':msg})}
        query = urllib.urlencode(params)
        path = os.path.join(layerurl, species_key_name)
        try:
            resource = _PutRequest(path, query)
            urllib2.urlopen(resource)
        except (Exception), e:
            logging.error('Unable to register error on App Engine: %s' % str(e))

    @staticmethod
    def validatepath(path, dir=True, read=True, write=False):
        """Raises a LayerError if the path is invalid.

        Arguments:
            path - the path to a file or directory
            dir = True if the path is a directory and False if it's a file
            read = True if the path must be readable otherwise False
            write = True if the path must be writable otherwise False
        """
        # Checks for a valid path value:
        if path is None or _isempty(path):
            raise LayerError('', 'The path was None or empty string')

        # Checks if the path exists:
        if not os.access(path, os.F_OK):
            logging.error(path)
            raise LayerError(path, 'The path does not exist: ' + path)

        # Checks for a valid directory:
        if dir:
            if not os.path.isdir(path):
                raise LayerError('', 'The path is not a directory: %s' % path)
        else:
            if not os.path.isfile(path):
                raise LayerError('', 'The path is not a file: %s' % path)

        # Checks for valid readability and writability:
        if read and not os.access(path, os.R_OK):
            raise LayerError('', 'The path is not readable: %s' % path)
        if write and not os.access(path, os.W_OK):
            raise LayerError('', 'The path is not writable: %s' % path)

    @staticmethod
    def isidvalid(id, url):
        """Returns True if the id is successfully validated against the GAE
        web service, otherwise returns False.
        """
        
        if id is None or _isempty(id):
            return False

        # Validates id against GAE web service:
        resource = "%s/%s" % (url, id)
        code = None
        try:
            code = urllib2.urlopen(resource).code
        except (HTTPError), e:
            logging.error(str(e))
            code = e.code
        except (Exception), e:
            logging.error(str(e))

        if code == 200:
            return True
        else:
            return False

    @staticmethod
    def idfrompath(path):
        """Returns the id for a path which is the root filename of the path
        without the extension. For example, 'foo' is the id for path
        '/bar/baz/foo.txt'.
        """
        # Checks for a valid path value:
        if path is None or _isempty(path):
            raise LayerError('', 'The path was None or empty string')
        Layer.validatepath(path, dir=False)
        tail = os.path.split(path)[1]
        root = os.path.splitext(tail)[0]
        return root, os.path.split(path)[0]


    def __init__(self, path, tiledir, errdir, srcdir, dstdir, mapfile, tileurl,
                 layerurl, valididurl, zoom=1, converted=False, tiled=False, type='expert',
                 status='accepted'):
        '''Constructs a new Layer object.'''
        
        # Validates argument values:
        if path is None or _isempty(path):
            raise LayerError('', 'The path was null or empty string')
        if tiledir is None or _isempty(tiledir):
            raise LayerError('', 'The tiledir was null or empty string')
        if errdir is None or _isempty(errdir):
            raise LayerError('', 'The errdir was null or empty string')
        if srcdir is None or _isempty(srcdir):
            raise LayerError('', 'The srcdir was null or empty string')
        if dstdir is None or _isempty(dstdir):
            raise LayerError('', 'The dstdir was null or empty string')

        # Validates the layer file path and directories:
        Layer.validatepath(path, dir=False)
        Layer.validatepath(tiledir, write=True)
        Layer.validatepath(errdir, write=True)
        Layer.validatepath(srcdir)
        Layer.validatepath(dstdir, write=True)
        Layer.validatepath(mapfile, dir=False, write=True)

        # Sets properties with the argument values:
        self.path = path
        self.tiledir = tiledir
        self.errdir = errdir
        self.srcdir = srcdir
        self.dstdir = dstdir
        self.mapfile = mapfile
        self.tileurl = tileurl
        self.layerurl = layerurl
        self.zoom = zoom
        self.converted = converted
        self.tiled = tiled
        self.meta = None
        self.status = status
        self.type = type
        self.valididurl = valididurl

        # Sets the layer id:
        self.id, self.srcdir = Layer.idfrompath(path)
        # Validate id
        if not Layer.isidvalid('animalia/species/%s' % self.id, valididurl):
            raise SpeciesIdError()
        logging.info('Layer id validated by frontend server')

        # TODO: This class handles shapefiles now, not asc
        # Sets the asc file path for this layer:
        # filename = '%s.asc' % self.id
        # self.ascfilepath = os.path.join(ascdir, filename)

        # Sets the tile directory for this layer:
        dirpath = os.path.join(tiledir, self.id)
        if not os.path.exists(dirpath):
            try:
                os.mkdir(dirpath)
            except (OSError), e:
                raise LayerError(e.strerror, e.strerror)
        self.mytiledir = dirpath

        # Sets the error log file:
        dirpath = os.path.join(errdir, '%s.log' % self.id)
        self.errlog = open(dirpath, 'w')
        
        
        #a first attempt at dynamic zoom control
        dynamicZoom = True
        self.meta, extents = _GdalUtil.getmetadata(self.path)
        if dynamicZoom:
            x = extents[1] - extents[0]
            y = extents[3] - extents[2]
            z = 0
            maxDim = max(x, y)
            zMod = 4 + int(6378136.0 / maxDim)
            while 2 ** z < zMod:
                z += 1
            self.zoom = z + 4
            logging.info("zoom %s: %s" % (z, self.id))
            
    def register(self):
        """Returns True if the layer metadata was successfully sent to App Engine
        for an update, otherwise returns False.
        """
        if self.meta is None:
            return False
        params = {'zoom': self.zoom,
                  'proj' : self.meta['proj'],
                  'dateCreated' : str(datetime.datetime.now()),
                  'maxLat' : str(self.meta['geog']['maxLat']),
                  'minLat' : str(self.meta['geog']['minLat']),
                  'maxLon' : str(self.meta['geog']['maxLon']),
                  'minLon' : str(self.meta['geog']['minLon']),
                  'type' : self.type,
                  'status' : self.status,
                  'remoteLocation' : self.tileurl % self.id,
                  }
        logging.info('Layer params for registration: %s' % str(params))
        query = urllib.urlencode(params)
        path = os.path.join(self.layerurl, 'animalia/species', self.id)
        response = None
        try:
            resource = _PutRequest(path, query)
            response = urllib2.urlopen(resource)
            return response is not None and response.code in [201, 204]
        except (HTTPError), e:
            if e.code == 409:
                logging.info('Metadata not updated (newer data exsits on frontend server)')
                return False
            else:
                raise e
        except (Exception), e:
            logging.error('Unable to register metadata: %s' % str(e))
            return False

    def dbtiles(self):
        """Stores tiles in the database."""
        # TODO
        raise NotImplementedError()

    def cleanup(self, error=None, delete_test=False):
        '''Cleans up filesystem depending on if there were errors or not.
        
        Arguments:
            error - an error if one occurred
            delete_test - deletes test source data if true (for testing only)
        '''

        src_dir, filename = os.path.split(self.path)
        
        logging.info('The src directory for cleanup ' + src_dir)

        if error is not None:
            # Copies files to errors directory for additional processing:
            err_dir = os.path.join(self.errdir, 'animalia/species')
            if os.path.exists(err_dir):
                for root, dirs, files in os.walk(err_dir):
                    for f in files:
                        os.unlink(os.path.join(root, f))
                    for d in dirs:
                        shutil.rmtree(os.path.join(root, d))
            for file in os.listdir(src_dir):
                if file.startswith(self.id):
                    shutil.copy2(os.path.join(src_dir, file), err_dir)

            # Deletes files from the tiles dir:
            tiles_dir = os.path.join(self.tiledir, 'animalia/species', self.id)
            if os.path.exists(tiles_dir):
                shutil.rmtree(tiles_dir)

            # Deletes files from the destination (grid) dir:
            #if os.path.exists(dst_dir):
            #    shutil.rmtree(dst_dir)

        else:
            # Copies files to destination directory for archival:            
            dst_dir = os.path.join(self.dstdir, 'animalia/species')
            for file in os.listdir(src_dir):
                if file.startswith(self.id):
                    shutil.copy2(os.path.join(src_dir, file), dst_dir)

            # Deletes files from the watched directory:
            if delete_test:
                logging.info('Deleting files from /ftp/new directory')
                for file in os.listdir(src_dir):
                    if file.startswith(self.id):
                        os.remove(os.path.join(src_dir, file))
            else:
                logging.info('Not deleting files from /ftp/new directory')

    def totiles(self, g):
        """Creates tiles for zoom + 1. Note that this method blocks."""
        """
        # Creates the GeoTiff if it doesn't already exist:
        if not self.converted:
            self.toasc()
        """
        tiles_dir = os.path.join(self.tiledir, 'animalia/species', self.id)
        if os.path.exists(tiles_dir):
            shutil.rmtree(tiles_dir)
            
        if self.meta is None:
            #self.meta = _GdalUtil.getmetadata(self.srcdir + '/' + self.id + '.shp')
            self.meta = _GdalUtil.getmetadata(self.path)

        tmp_xml = open(self.mapfile, 'r').read().replace('layer_name', self.id)
        mapfile = self.srcdir + '/' + self.id + '.xml'
        open(mapfile, "w+").write(tmp_xml)

        a, b, x, y = self.meta['geog']['minLon'], self.meta['geog']['minLat'], self.meta['geog']['maxLon'], self.meta['geog']['maxLat']

        bbox = (a,
                b,
                x,
                y)
        
        GenerateTiles.render_tiles(bbox,
                                   mapfile,
                                   self.mytiledir.rstrip('/') + "/",
                                   0,
                                   #g.TILE_MAX_ZOOM,
                                   self.zoom,
                                   "MOL-EORM",
                                   num_threads=g.TILE_QUEUE_THREADS + 0)

        """
        self.tiling = subprocess.Popen(
            ["java",
            "-mx300m",
            "-classpath",
            "/raster/classes:/raster/lib/maxent.jar",
            "-Djava.awt.headless=true",
            "raster/GridToGoogle",
            self.ascfilepath,
            self.mytiledir,
            str(self.zoom + 1)
            ], stderr=self.errlog)
        # Waits for the tiling process to finish:
        self.tiling.wait()
        """

    def toasc(self):
        """Converts layer to a GeoTiff. Note that this method blocks."""

        # Creates a GeoTiff:
        self.translating = subprocess.Popen(
            ["gdal_translate",
            "-of",
            "AAIGrid",
            "-a_srs",
             "epsg:900913",
             self.path,
             self.ascfilepath
            ], stderr=self.errlog)

        # Waits for GeoTiff creation process to finish:
        self.translating.wait()

        # FIXME: May not have been converted if there were errors:
        self.converted = True

        if self.meta is None:
            self.meta = _GdalUtil.getmetadata(self.path)
