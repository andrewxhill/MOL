#!/usr/bin/env python
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
from osgeo import gdal
from urllib2 import HTTPError
import datetime
import os.path
import shutil
import subprocess
import urllib
import urllib2

GAE_URL = "http://localhost:8080/"
VALID_ID_SERVICE_URL = "%sapi/validid" % GAE_URL
LAYER_UPDATE_SERVICE_URL = "%sapi/layer/update" % GAE_URL
REMOTE_SERVER_TILE_LOCATION = 'http://mol.colorado.edu/tiles/%s/zoom/x/y.png'

class Error(Exception):
    """Base class for exceptions in this module."""
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

def _isempty(s):
    return len(s.strip()) == 0
    
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
        return {'maxLat': max(list(geotrans)[1::2]), 'minLat': min(list(geotrans)[1::2]), 'maxLon': max(list(geotrans)[0::2]), 'minLon': min(list(geotrans)[0::2])}
    
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
        ascdata = gdal.Open(filepath)
        if ascdata is None:
            return None
        projection = ascdata.GetProjection()
        geotrans = ascdata.GetGeoTransform()        
        bb = _GdalUtil.getboundingbox(geotrans)
        return {'proj' : projection, 'geog': bb}
    
class Layer(object):         
        
    @staticmethod
    def isidvalid(id):
        """Returns True if the id is successfully validated against the GAE
        web service, otherwise returns False.
        """
        # Validates the id value:
        if id is None or _isempty(id):
            return False
        
        # Validates id against GAE web service:
        params = {'id': id}
        resource = "%s?%s" % (VALID_ID_SERVICE_URL, urllib.urlencode(params))
        code = None
        try:
            code = urllib2.urlopen(resource).code
        except HTTPError as e:            
            code = e.code
        
        if code == 200:
            return True
        if code == 404:
            return False
        
        return False
        # TODO: how to handle other response codes?
        
    @staticmethod
    def idfrompath(path):
        """Returns the id for a path which is the root filename of the path 
        without the extension. For example, 'foo' is the id for path 
        '/bar/baz/foo.txt'.
        """
        # Checks for a valid path value:
        if path is None or _isempty(path):
            raise LayerError('', 'The path was None or empty string')
        Layer.validatepath(path)
        tail = os.path.split(path)[1]
        root = os.path.splitext(tail)[0]
        return root
        
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
            raise LayerError('', 'The path does not exist: %s' % path)    
    
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
    
    def __init__(self, path, tiledir, ascdir, errdir, srcdir, dstdir, zoom=1,
                 converted=False, tiled=False):   
        """Constructs a new Layer object.
        
        Arguments:
            path - filesystem path of a directory containing raster layer data
            TODO...
        """
        # Validates argument values:
        if path is None or _isempty(path):
            raise LayerError('', 'The path was null or empty string')        
        if tiledir is None or _isempty(tiledir):
            raise LayerError('', 'The tiledir was null or empty string')
        if ascdir is None or _isempty(ascdir):
            raise LayerError('', 'The ascdir was null or empty string')
        if errdir is None or _isempty(errdir):
            raise LayerError('', 'The errdir was null or empty string')
        if srcdir is None or _isempty(srcdir):
            raise LayerError('', 'The srcdir was null or empty string')        
        if dstdir is None or _isempty(dstdir):
            raise LayerError('', 'The dstdir was null or empty string')        
                            
        # Validates the layer file path and directories:
        Layer.validatepath(path)
        Layer.validatepath(tiledir, write=True)        
        Layer.validatepath(ascdir, write=True)        
        Layer.validatepath(errdir, write=True)        
        Layer.validatepath(srcdir)        
        Layer.validatepath(dstdir, write=True)        
        
        # Sets properties with the argument values:
        self.path = path    
        self.tiledir = tiledir        
        self.ascdir = ascdir
        self.errdir = errdir
        self.srcdir = srcdir
        self.dstdir = dstdir
        self.zoom = zoom
        self.converted = converted
        self.tiled = tiled
        
        # Sets the layer id:
        self.id = Layer.idfrompath(path)

        # Sets the asc file path for this layer:
        filename = '%s.asc' % self.id
        self.ascfilepath = os.path.join(ascdir, filename)
        
        # Sets the tile directory for this layer:
        dirpath = os.path.join(tiledir, self.id)
        if not os.path.exists(dirpath):
            try:
                os.mkdir(dirpath)
            except OSError as e:
                raise LayerError(e.strerror, e.strerror)
        self.mytiledir = dirpath
                
        # Sets the error log file:
        dirpath = os.path.join(errdir, '%s.log' % self.id)
        self.errlog = open(dirpath, 'w')
    
    def register(self):
        """Returns True if the layer metadata was successfully sent to App Engine
        for an update, otherwise returns False.
        
        Arguments:
            layer - a Layer object to update
        """
        meta = _GdalUtil.getmetadata(self.ascfilepath)
        if meta is None:
            return False
        
        # Builds URL request params:
        params = {'id': self.id,
                  'zoom': self.zoom,
                  'proj' : meta['proj'],
                  'date' : str(datetime.datetime.now()),
                  'maxLat' : str(meta['geog']['maxLat']),
                  'minLat' : str(meta['geog']['minLat']),
                  'maxLon' : str(meta['geog']['maxLon']),
                  'minLon' : str(meta['geog']['minLon']),
                  'remoteLocation' : REMOTE_SERVER_TILE_LOCATION % self.id
                  }
        query = urllib.urlencode(params)
        
        # Builds and sends the request:
        resource = urllib2.Request(LAYER_UPDATE_SERVICE_URL, query)
        response = urllib2.urlopen(resource)
        return True
        # TODO(Aaron): Handling the response is pending a REST API change
        # return response.code == 204
    
    def dbtiles(self):
        """Stores tiles in the database."""
        # TODO
        raise NotImplementedError()

    def cleanup(self):
        """Cleans up directories."""
        files = [self.ascfilepath,
                 self.ascfilepath.replace('.asc', '.prj')]
        for file in files:
            try:
                os.remove(file)
            except:
                pass
        try:
            shutil.rmtree(self.dstdir + self.id)
        except:
            pass
        try:
            shutil.copytree(self.path, self.dstdir + self.id)
        except:
            pass
        try:
            shutil.rmtree(self.srcdir + self.id)
        except:
            pass
            
    def totiles(self):
        """Creates tiles for zoom + 1. Note that this method blocks."""
        # Creates the GeoTiff if it doesn't already exist:
        if not self.converted:
            self.toasc()
            
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
