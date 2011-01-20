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
from osgeo import gdal
import Queue
import datetime
import os
import shutil
import simplejson
import subprocess
import threading
import urllib
import urllib2
from urllib2 import URLError, HTTPError

GAE_URL = "http://localhost:8080/"

worker_q = Queue.Queue()

class BulkLoadTiles():
    """class for running the bulkloader to upload tilesets to GAE"""
    def __init__(self, id=None):
        self.id = id
        
    def uploadTiles(self):
        pass
        
class Layer():
    zoom = 1 #sets the maximum zoom we want to process
    info = {}
    errors = []
    converted = False
    tiled = False
    tileDir = "/ftp/tiles/" #/some/tmp/folder/for/tiles/
    ascDir = "/ftp/asc/" #/some/tmp/folder/for/asc/
    errDir = "/ftp/errors/"
    srcDir = "/ftp/newraster/"
    dstDir = "/ftp/grid/"
    idIsValid = False
    
    def __init__(self, fullpath=None):
        
        """raster: string filename of file to process"""
        print 'FULLPATH: %s' % fullpath
        (dirname, filename) = os.path.split(fullpath)
        (basename, fileext) = os.path.splitext(filename)
        if filename is not None:
            self.origRaster = fullpath
            self.id = basename
            self.tileFolder = self.tileDir + self.id
            self.ascName = self.ascDir + "%s.asc" % self.id
            self.nulfp = open(self.errDir + '%s.log' % self.id, 'w')
            print self.__dict__
        
    def verifyId(self):
        """Verifies the layer id using a web service on GAE that returns 200 for 
        a valid id and a 404 for invalid id.
        """
        params = {'id': self.id}
        resource = "%sapi/validid?%s" % (GAE_URL, urllib.urlencode(params))
        try:
            urllib2.urlopen(resource)
            return True
        except HTTPError as e:            
            print 'URLError: %s' % e.code  
            return False

    def getInfo(self, fn):
        #use gdalinfo= to populate an info object
        layer = gdal.Open(fn)
        self.info['id'] = self.id
        self.info['zoom'] = self.zoom
        self.info['date'] = datetime.datetime.now()
        self.info['proj'] = layer.GetProjection()
        geog = layer.GetGeoTransform()
        #temp holder, should parse from the geog object above
        self.info['geog'] = {'maxLat': 1.4,
                             'minLat': 1.2,
                             'maxLon': 1.4,
                             'minLon': 1.2}
        return True
        
    def convertToASC(self):
        #create a geotiff
        self.translating = subprocess.Popen(
            ["gdal_translate",
            "-of",
            "AAIGrid",
            "-a_srs",
             "epsg:900913",
             self.origRaster,
             self.ascName
            ], stderr=self.nulfp)
        self.translating.wait()
        self.converted = True
        self.getInfo(self.ascName)
        
    def tile(self):
        if not self.converted:
            self.convertToASC()
            
        self.tiling = subprocess.Popen(
            ["java",
            "-mx300m",
            "-classpath",
            "/raster/classes:/raster/lib/maxent.jar",
            "-Djava.awt.headless=true",
            "raster/GridToGoogle",
            self.ascName,
            self.tileFolder,
            str(self.zoom + 1)
            ], stderr=self.nulfp)
        self.tiling.wait()
        
    def registerMetadata(self):
        #send metadata to GAE
        params = {'id': self.id,
                  'zoom': self.zoom,
                  'proj': self.info['proj'],
                  'date': str(datetime.datetime.now()),
                  'maxLat': str(self.info['geog']['maxLat']),
                  'minLat': str(self.info['geog']['minLat']),
                  'maxLon': self.info['geog']['maxLon'],
                  'minLon': self.info['geog']['minLon'],
                  'remoteLocation': 'http://mol.colorado.edu/tiles/%s/zoom/x/y.png' % self.id}
        resource = urllib2.Request("%sapi/layer/update" % GAE_URL, urllib.urlencode(params))
        response = urllib2.urlopen(resource)
        out = response.read()
        # TODO: Log out and response
        
    def storeTiles(self):
        #TODO: store tiles in couchdb
        return True
    
    def cleanup(self):
        files = [self.ascName,
                 self.ascName.replace('.asc', '.prj')]
        for file in files:
            try:
                os.remove(file)
            except:
                pass
        try:
            shutil.rmtree(self.dstDir + self.id)
        except:
            pass
        try:
            shutil.copytree(self.origRaster, self.dstDir + self.id)
        except:
            pass
        try:
            shutil.rmtree(self.srcDir + self.id)
        except:
            pass
        
            
class LayerProcessingThread(threading.Thread):
    def run(self):
        print 'Worker thread is running.'
 
        while True:
            data = worker_q.get()
            if data['jobtype'] == 'newraster':
                fullpath = data['fullpath']
                try:
                    # do task
                    layer = Layer(fullpath=fullpath)
                    layer.convertToASC()
                    layer.tile()
                    layer.registerMetadata()
                    layer.cleanup()
                    print 'We got %s tiles, do something with them!' % (fullpath)
                except Exception, e:
                    print 'Unable to process in worker thread: ' + str(e)
                worker_q.task_done()    
                
            elif data['jobtype'] == 'bulkload-tiles': 
                """run the BulkLoadTiles class above"""
                pass
 
def start_myworker():
    worker = LayerProcessingThread()
    worker.start()
    
