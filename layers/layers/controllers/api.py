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
from pylons import response, request, app_globals
from layers.lib.base import *
from layers.lib.mol.service import GenerateTile, GenerateOverview
import logging
import os
import simplejson
import math
import urllib
import urllib2


log = logging.getLogger(__name__)


OVERVIEW_BACKGROUND = 'steelblue'
OVERVIEW_POLYGON = '#f2eff9'
OVERVIEW_LINE = 'rgb(50%,50%,50%)'
OVERVIEW_LINE_WIDTH = 0.1


def bboxfromxyz(x,y,z):             
    pixels = 256
    
    res = (2 * math.pi * 6378137 / pixels) / (2**int(z))
    sh = 2 * math.pi * 6378137 / 2.0

    gy = (2**float(z) - 1) - int(y)
    minx, miny = ((float(x)*pixels) * res - sh),      (((float(gy))*pixels) * res - sh)
    maxx, maxy = (((float(x)+1)*pixels) * res - sh),  (((float(gy)+1)*pixels) * res - sh)
    
    minx, maxx = (minx / sh) * 180.0, (maxx / sh) * 180.0
    miny, maxy = (miny / sh) * 180.0, (maxy / sh) * 180.0
    miny = 180 / math.pi * (2 * math.atan( math.exp( miny * math.pi / 180.0)) - math.pi / 2.0)
    maxy = 180 / math.pi * (2 * math.atan( math.exp( maxy * math.pi / 180.0)) - math.pi / 2.0)
    return minx,miny,maxx,maxy
        
class ApiController(BaseController):
    
    def testid(self):
        id = request.params.get('id', None)
        url = request.params.get('url', None)
        return simplejson.dumps({'species_id':id, 'valid':Layer.isidvalid(id, url)})
    
    def overview(self, id):
        datatype = id
        id = request.params.get('id', None)
        w = request.params.get('w', 256)
        h = request.params.get('h', 256)
        
        params = {
                "background": request.params.get('background', OVERVIEW_BACKGROUND),
                "polygon": request.params.get('polygon', OVERVIEW_POLYGON),
                "line": request.params.get('line', OVERVIEW_LINE),
                "line-width": request.params.get('linewidth', OVERVIEW_LINE_WIDTH)
                }
                
        if datatype=="ecoregion":
            overview = os.path.join('/ftp/overviews/', id + '.png')
            shpfile = os.path.join('/ftp/ecoregion/shp/', id + '.shp')
            proj = "+proj=latlong +datum=WGS84"
            
        elif datatype=="pa":
            overview = os.path.join('/ftp/overviews/', id + '.png')
            shpfile = os.path.join('/ftp/pa/shp/', id + '.shp')
            proj = "+proj=latlong +datum=WGS84"
            
        GenerateOverview.render(id, overview, shpfile, proj, w, h, params)
        
        try:
            logging.info('Returning tile : ' + overview)
            response.headers['Content-Type'] = 'image/png'
            response.status = 200
            return open(overview, 'rb').read()
        except:
            response.status = 404
            return None
        
        
        
    def newtileset(self, id):
        datatype = id
        '''For any new tileset that the frontend wants to create, this needs to be initiated.
           It creates a mapfile.xml for the given dataset so that future tiling jobs can be 
           run based on the tileset id (param 'id') alone instead of resending the full set
           of layers included 
           
           parameters:
           
           id - the unique id for the given tileset, uniqueness needs only be maintained within 
                a source type. E.g. there can be an ecoregion tileset named puma_concolor and a
                range tileset named puma_concolor with no conflict
                
           range_ids - if the type=range, it will look for this comma delimited set of range
                ids to base the tileset off of. Any that are not found to be real shp files 
                will be ignored, if none are found to be real shp files a 404 will be returned
           region_ids - same as range_ids but for type=ecoregion.
           
           example:
           
           http://mol.colorado.edu/layers/api/newtileset/range?id=animalia/species/puma_concolor&range_ids=animalia/species/puma_concolor
           
        '''
           
        id = request.params.get('id', None)
        
        if datatype=="range":
            ids = request.GET['range_ids'].split(',')
            shpdir = app_globals.RANGESHP_DIR
            mapfile = os.path.join(app_globals.RANGESHP_DIR, id + '.mapfile.xml')  
            proj = "+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext +over +no_defs"
            
        elif datatype=="ecoregion":
            ids = request.GET['region_ids'].split(',')
            shpdir = app_globals.ECOSHP_DIR
            mapfile = os.path.join(app_globals.ECOSHP_DIR, id + '.mapfile.xml') 
            proj = "+proj=latlong +datum=WGS84"
            
        elif datatype=="pa":
            ids = request.GET['region_ids'].split(',')
            shpdir = app_globals.PASHP_DIR
            mapfile = os.path.join(app_globals.PASHP_DIR, id + '.mapfile.xml') 
            proj = "+proj=latlong +datum=WGS84"
            
        mf = NewMapfile()
        
        
        logging.info('Creating tileset type: ' + datatype)
        logging.info('Creating tileset id: ' + id)
        logging.info('Creating tileset containing: ' + ','.join(ids))
        
        
        for f in ids:        
            if os.path.exists(os.path.join(shpdir, f + '.shp')):
                logging.info('Dataset ' + id +': valid')
                mf.newfeature(f,os.path.join(shpdir, f + '.shp'),proj)
            else:
                logging.info('Dataset ' + id +': invalid')
        
        if mf.features > 0:
            mf.savefile(mapfile)
            logging.info('Creating tileset id ' + id + ': created')
            response.status = 200
        else:
            logging.info('Creating tileset id ' + id + ': not created')
            response.status = 404
        return
            
            
    def tile(self, id):
        datatype = id
        x = request.params.get('x', None)
        y = request.params.get('y', None)
        z = request.params.get('z', None)
        id = request.params.get('id', None)
        overwrite = True if request.params.get('overwrite', None) is not None else False
        
        logging.info('Creating tileset type: ' + datatype)
        
        if datatype=="range":
            mapfile = os.path.join(app_globals.RANGESHP_DIR, id + '.mapfile.xml')  
            tile_dir = os.path.join(app_globals.TILE_DIR, id)    
            tile = os.path.join(tile_dir, z, x, "%s.png" % y)  
            null_tile = os.path.join(tile_dir, z, x, "%s.null" % y)  
            empty_bytes=334
            
        elif datatype=="ecoregion":
            mapfile = os.path.join(app_globals.ECOSHP_DIR, id + '.mapfile.xml')   
            tile_dir = os.path.join(app_globals.ECOTILE_DIR, id)   
            tile = os.path.join(tile_dir, z, x, "%s.png" % y)  
            null_tile = os.path.join(tile_dir, z, x, "%s.null" % y)  
            empty_bytes=334
            
        elif datatype=="pa":
            mapfile = os.path.join(app_globals.PASHP_DIR, id + '.mapfile.xml')   
            tile_dir = os.path.join(app_globals.PATILE_DIR, id)   
            tile = os.path.join(tile_dir, z, x, "%s.png" % y)  
            null_tile = os.path.join(tile_dir, z, x, "%s.null" % y)  
            empty_bytes=334
            
        logging.info('Generating new ' + datatype +' tile: ' + id)
        
        if os.path.isfile(tile) and overwrite is False:
            logging.info('Returning existing tile: ' + tile)
            response.headers['Content-Type'] = 'image/png'
            response.status = 200
            return open(tile, 'rb').read()
        elif os.path.isfile(null_tile) and overwrite is False:
            logging.info('No tile: ' + tile)
            response.status = 204
            del response.headers['content-type']
            return None
            
        elif not os.path.exists(mapfile):
            logging.info('No mapfile : ' + mapfile)
            response.status = 404
            return None
        else:
            if not os.path.isdir(tile_dir):
                logging.info('Making directories')
                os.makedirs(tile_dir)
            
            logging.info('Creating tiles')
            tilestatus = GenerateTile.render(str(id), 
                                str(tile_dir),
                                str(mapfile), 
                                int(x), 
                                int(y), 
                                int(z), 
                                overwrite=overwrite,
                                empty_bytes=empty_bytes)
            
            if tilestatus == 204:
                response.status = 204
                del response.headers['content-type']
                return None
            elif tilestatus:
                logging.info('Returning tile : ' + tile)
                response.headers['Content-Type'] = 'image/png'
                response.status = 200
                return open(tile, 'rb').read()
            else:
                response.status = 404
                return None
        
        
    def tiles(self, id):
        datatype = id
        x = request.params.get('x', None)
        y = request.params.get('y', None)
        z = request.params.get('z', None)
        id = request.params.get('id', None)
        
        overwrite = True if request.params.get('overwrite', None) is not None else False
        
        logging.info('Creating tileset type: ' + datatype)
        
        if datatype=="range":
            mapfile = os.path.join(app_globals.RANGESHP_DIR, id + '.mapfile.xml')  
            if not os.path_exists(mapfile):
                url = "http://mol.colorado.edu/layers/api/newtileset/range?id=%s&range_ids=%s" % (id,id)
                req = urllib2.Request(url)
                response = urllib2.urlopen(req)
            tile_dir = os.path.join(app_globals.TILE_DIR, id)    
            tile = os.path.join(tile_dir, z, x, "%s.png" % y)  
            null_tile = os.path.join(tile_dir, z, x, "%s.null" % y)  
            
        elif datatype=="ecoregion":
            mapfile = os.path.join(app_globals.ECOSHP_DIR, id + '.mapfile.xml')   
            tile_dir = os.path.join(app_globals.ECOTILE_DIR, id)   
            tile = os.path.join(tile_dir, z, x, "%s.png" % y)  
            null_tile = os.path.join(tile_dir, z, x, "%s.null" % y)  
            
        logging.info('Generating new ' + datatype +' tiles: ' + id)
        bbox = bboxfromxyz(int(x),int(y),int(z) )   
        GenerateTiles.render_tiles(bbox,
                                   str(mapfile),
                                   str(tile_dir),
                                   int(z),
                                   int(z+1),
                                   str(id),
                                   num_threads=app_globals.TILE_QUEUE_THREADS,
                                   overwrite=overwrite)   
        
