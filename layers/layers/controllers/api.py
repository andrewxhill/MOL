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
from layers.lib.base import BaseController
from layers.lib.taskqueue import worker_q
from layers.lib.mol.service import GenerateTiles
from pylons import response, request, app_globals
import logging
import os
os.environ["CELERY_CONFIG_MODULE"] = "layers.cando.settings"
import simplejson
from layers.lib.mol.service import Layer
#from layers.cando.tiling.tasks import EcoregionProcessingThread
import math


log = logging.getLogger(__name__)

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

class NewMapfile():
    def __init__(self):
        self.header = """<?xml version="1.0" encoding="utf-8"?>
                                <!DOCTYPE Map>
                                <Map bgcolor="transparent" srs="+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext +over +no_defs">
                                  <Style name="style">
                                    <Rule>
                                      <PolygonSymbolizer>
                                        <CssParameter name="fill">#000000</CssParameter>
                                      </PolygonSymbolizer>
                                      <LineSymbolizer>
                                        <CssParameter name="stroke">#000000</CssParameter>
                                        <CssParameter name="stroke-width">0.0</CssParameter>
                                      </LineSymbolizer>
                                    </Rule>
                                  </Style>"""
        self.body = ""
        self.footer = """</Map>"""
        self.features = 0
        
    def newfeature(self,name,src,proj):
        self.features +=1
        tmp_xml += """
                <Layer name="layer_name" srs="projection_string">
                <StyleName>style</StyleName>
                <Datasource>
                  <Parameter name="type">shape</Parameter>
                  <Parameter name="file">layer_src</Parameter>
                </Datasource>
              </Layer>""".replace("layer_name",name).replace("layer_src",src).replace("projection_string", proj)
        self.body = self.body + tmp_xml
        return True
    
    def returnfile(self):
        return self.header + self.body + self.footer
    
    def savefile(self, filepath):
        f = open(fileopen, "w+")
        f.write(self.returnfile())
        f.close()
        return True
        
        
class ApiController(BaseController):
    
    def testid(self):
        id = request.params.get('id', None)
        url = request.params.get('url', None)
        return simplejson.dumps({'species_id':id, 'valid':Layer.isidvalid(id, url)})
    
    def newtileset(self, id):
        type = id
        logging.info('Creating tileset : ' + type)
        '''For any new tileset that the frontend wants to create, this needs to be initiated.
           It creates a mapfile.xml for the given dataset so that future tiling jobs can be 
           run based on the tileset id (param 'id') alone instead of resending the full set
           of layers included 
           
           parameters
           
           id - the unique id for the given tileset, uniqueness needs only be maintained within 
                a source type. E.g. there can be an ecoregion tileset named puma_concolor and a
                range tileset named puma_concolor with no conflict
                
           range_ids - if the type=range, it will look for this comma delimited set of range
                ids to base the tileset off of. Any that are not found to be real shp files 
                will be ignored, if none are found to be real shp files a 404 will be returned
           region_ids - same as range_ids but for type=ecoregion.
           
        '''
           
        id = request.params.get('id', None)
        
        if type=="range":
            ids = request.GET['range_ids'].split(',')
            shpdir = app_globals.RANGESHP_DIR
            mapfile = os.path.join(app_globals.RANGESHP_DIR, id, '.mapfile.xml')  
            proj = "+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext +over +no_defs"
            
        elif type=="ecoregion":
            ids = request.GET['region_ids'].split(',')
            shpdir = app_globals.ECOSHP_DIR
            mapfile = os.path.join(app_globals.ECOSHP_DIR, id, '.mapfile.xml') 
            proj = "+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext +over +no_defs"
        
        mf = NewMapfile()
        
        for f in ids:        
            if os.path.exists(os.path.join(shpdir, f + '.shp')):
                mf.newfeature(f,os.path.join(shpdir, f + '.shp'),proj)
        
        if mf.features > 0:
            mf.savefile(mapfile)
            response.status = 200
        else:
            response.status = 404
        return
            
            
    def tile(self, type):
        x = request.params.get('x', None)
        y = request.params.get('y', None)
        z = request.params.get('z', None)
        id = request.params.get('id', None)
        
        if type=="range":
            mapfile = os.path.join(app_globals.RANGESHP_DIR, id, '.mapfile.xml')  
            tile_dir = os.path.join(app_globals.TILE_DIR, id)    
            tile = os.path.join(tile_dir, z, x, "%s.png" % y)  
            
        elif type=="ecoregion":
            mapfile = os.path.join(app_globals.ECOSHP_DIR, id, '.mapfile.xml')   
            tile_dir = os.path.join(app_globals.ECOTILE_DIR, id)   
            tile = os.path.join(tile_dir, z, x, "%s.png" % y)  
        
        if os.path.exists(tile):
            logging.info('Returning tile : ' + tile)
            response.headers['Content-Type'] = 'image/png'
            response.status = 200
            return open(tile, 'rb').read()
            
        if not os.path.exists(mapfile):
            response.status = 404
            return
            
        logging.info('Creating mapfile: %s' % (mapfile))  
        minx, miny, maxx, maxy = bboxfromxyz(x, y, z)
        bbox = (minx, miny, maxx, maxy)
        
        if not os.path.isdir(tile_dir):
            os.mkdir(tile_dir)
        GenerateTiles.render_tiles(bbox,
                                   mapfile,
                                   tile_dir,
                                   int(z),
                                   int(z),
                                   name,
                                   num_threads=app_globals.TILE_QUEUE_THREADS,
                                   overwrite=overwrite)   
            
        if os.path.exists(tile):
            logging.info('Returning tile : ' + tile)
            response.headers['Content-Type'] = 'image/png'
            response.status = 200
            return open(tile, 'rb').read()
        else:
            response.status = 404
            return
        
        
    def tiles(self, species_id, zoom, x, y):
        '''OLD METHOD, DO NOT USE ANYMORE'''
        '''This action returns PNG data with the response header Content-Type 
        set to image/png with a 200 status code. It handles URLs of the form:
        
        http://mol.colorado.edu/tiles/species_id/zoom/x/y.png
        
        If a tile isn't found a 404 status is returned.
        '''
        png = os.path.join(app_globals.TILE_DIR, species_id, zoom, x, y + '.png')        
        if os.path.exists(png):
            logging.info('Returning tile : ' + png)
            response.headers['Content-Type'] = 'image/png'
            response.status = 200
            return open(png, 'rb').read()
        logging.info('Tile not found : ' + png)        
        response.status = 404
        
    def ecoregion(self, method, name):
        '''OLD METHOD, DO NOT USE ANYMORE'''
        if method=='tile':
            overwrite = False
            try:
                if str(request.GET['overwrite']).strip().lower() == 'true':
                    overwrite = True
            except:
                pass
            newmapfile = False
            try:
                if str(request.GET['newmapfile']).strip().lower() == 'true':
                    newmapfile = True
            except:
                pass
            logging.error(overwrite)
            x = request.GET['x']
            y = request.GET['y']
            z = request.GET['zoom']
            name = name.strip('.png')
            
            png = os.path.join(app_globals.ECOTILE_DIR, name, z, x, y + '.png')   
            nullPng = os.path.join(app_globals.ECOTILE_DIR, name, z, x, y + '.null') 
              
            if overwrite or (not os.path.exists(png) and not os.path.exists(nullPng)):
                try:
                    region_ids = request.GET['region_ids'].split(',')
                except:
                    region_ids = [name]
                tmp_xml = """<?xml version="1.0" encoding="utf-8"?>
                                <!DOCTYPE Map>
                                <Map bgcolor="transparent" srs="+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext +over +no_defs">
                                  <Style name="style">
                                    <Rule>
                                      <PolygonSymbolizer>
                                        <CssParameter name="fill">#000000</CssParameter>
                                      </PolygonSymbolizer>
                                      <LineSymbolizer>
                                        <CssParameter name="stroke">#000000</CssParameter>
                                        <CssParameter name="stroke-width">0.0</CssParameter>
                                      </LineSymbolizer>
                                    </Rule>
                                  </Style>"""
                mapfile = str(app_globals.ECOSHP_DIR +'/'+ name + '.mapfile.xml')
                
                logging.info('Creating mapfile: %s' % (mapfile))  
                
                minx, miny, maxx, maxy = bboxfromxyz(x, y, z)
                
                bbox = (minx, miny, maxx, maxy)
                
                logging.info('Tiling %s with bbox: %s' % (name,str(bbox)))  
                
                proj = "+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext +over +no_defs"
                ct=0
                for id in region_ids:
                    shp = os.path.join(app_globals.ECOSHP_DIR, id + '.shp')        
                    if os.path.exists(shp):
                        ct+=1
                        tmp_xml += """
                                <Layer name="layer_name" srs="projection_string">
                                <StyleName>style</StyleName>
                                <Datasource>
                                  <Parameter name="type">shape</Parameter>
                                  <Parameter name="file">layer_name</Parameter>
                                </Datasource>
                              </Layer>""".replace("layer_name",id).replace("projection_string", proj)
                        
                tmp_xml += "</Map>"
                if ct>0:
                    tile_dir =  str(app_globals.ECOTILE_DIR.rstrip('/') + "/" + name +"/")
                    if newmapfile or not os.path.exists(mapfile):
                        open(mapfile, "w+").write(tmp_xml)
                    if not os.path.isdir(tile_dir):
                        os.mkdir(tile_dir)
                    GenerateTiles.render_tiles(bbox,
                                               mapfile,
                                               tile_dir,
                                               int(z),
                                               int(z),
                                               name,
                                               num_threads=app_globals.TILE_QUEUE_THREADS,
                                               overwrite=overwrite)                    
            if os.path.exists(png):
                logging.error('Returning tile : ' + png)
                response.headers['Content-Type'] = 'image/png'
                response.status = 200
                return open(png, 'rb').read()
                
            logging.info('Tile not found : ' + png)        
            response.status = 404
            
        elif str(method).lower() == 'tilearea':
            """ Takes one to many record_ids split by commas and a unique
                name for the tileset you are creating.
                
                e.g., If you are creating a tileset for a single ecoregion
                with code NT105, you would probably want to create a new 
                tileset with,
                    name = 'NT105',
                    record_ids = 'NT105'
                If you are creating a new tileset for hyp. spec 'Andreus 
                andreus' you could create a tileset with,
                    name = 'animalia-mammalia-Andreus_andreus'
                    record_ids = 'NT103','NT445','NT6742'
            """
            
            try:
                region_ids = request.GET['region_ids'].split(',')
            except:
                region_ids = [name]
            lowx = request.GET['lowx']
            lowy = request.GET['lowy']
            highx = request.GET['highx']
            highy = request.GET['highy']
            zoom = int(request.GET['zoom'])
            
            request_ip = request.environ['REMOTE_ADDR']                
            #if request_ip == "127.0.0.1":
            if False:
                #executes nicely, but doesn't run as far as I can tell
                EcoregionProcessingThread.apply_async(args=[name, zoom, lowx, lowy, highx, highy, region_ids])
                logging.info('Sending job to Celery')
                response.status = 200   
                return
            else:
                logging.info("request from: %s" %request_ip)
                
                tile_dir =  str(app_globals.ECOTILE_DIR.rstrip('/') + "/" + name +"/")
                
                tmp_xml = """<?xml version="1.0" encoding="utf-8"?>
                                <!DOCTYPE Map>
                                <Map bgcolor="transparent" srs="+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext +over +no_defs">
                                  <Style name="style">
                                    <Rule>
                                      <PolygonSymbolizer>
                                        <CssParameter name="fill">#000000</CssParameter>
                                      </PolygonSymbolizer>
                                      <LineSymbolizer>
                                        <CssParameter name="stroke">#000000</CssParameter>
                                        <CssParameter name="stroke-width">0.0</CssParameter>
                                      </LineSymbolizer>
                                    </Rule>
                                  </Style>"""
                mapfile = str(app_globals.ECOSHP_DIR +'/'+ name + '.mapfile.xml')
                
                logging.info('Creating mapfile: %s' % (mapfile))  
                
                
                bbox = (float(lowx), float(lowy), float(highx), float(highy))
                logging.info('Tiling %s with bbox: %s' % (name,str(bbox)))  
                    
                proj = "+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext +over +no_defs"
                
                ct=0
                for id in region_ids:
                    shp = os.path.join(app_globals.ECOSHP_DIR, id + '.shp')        
                    if os.path.exists(shp):
                        ct+=1
                        tmp_xml += """
                                <Layer name="layer_name" srs="projection_string">
                                <StyleName>style</StyleName>
                                <Datasource>
                                  <Parameter name="type">shape</Parameter>
                                  <Parameter name="file">layer_name</Parameter>
                                </Datasource>
                              </Layer>""".replace("layer_name",id).replace("projection_string", proj)
                        
                tmp_xml += "</Map>"
                if ct>0:
                    open(mapfile, "w+").write(tmp_xml)
                    if not os.path.isdir(tile_dir):
                        os.mkdir(tile_dir)
                    GenerateTiles.render_tiles(bbox,
                                               mapfile,
                                               tile_dir,
                                               zoom,
                                               zoom,
                                               name,
                                               num_threads=app_globals.TILE_QUEUE_THREADS,
                                               overwrite=False)
                    response.status = 200   
                    return
                    
                logging.info('Regions not found : ' + shp)        
                response.status = 404
