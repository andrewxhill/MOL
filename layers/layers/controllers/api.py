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
import simplejson
from layers.lib.mol.service import Layer
import math

log = logging.getLogger(__name__)

class ApiController(BaseController):
    
    def testid(self):
        id = request.params.get('id', None)
        url = request.params.get('url', None)
        return simplejson.dumps({'species_id':id, 'valid':Layer.isidvalid(id, url)})        
    
    def tiles(self, species_id, zoom, x, y):
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
                
                bbox = (minx, miny, maxx, maxy)
                
                logging.info('Tiling %s with bbox: %s' % (name,str(bbox)))  
                    
                ct=0
                for id in region_ids:
                    shp = os.path.join(app_globals.ECOSHP_DIR, id + '.shp')        
                    if os.path.exists(shp):
                        ct+=1
                        tmp_xml += """
                                <Layer name="layer_name" srs="+proj=latlong +datum=WGS84">
                                <StyleName>style</StyleName>
                                <Datasource>
                                  <Parameter name="type">shape</Parameter>
                                  <Parameter name="file">layer_name</Parameter>
                                </Datasource>
                              </Layer>""".replace("layer_name",id)
                        
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
                
            ct=0
            for id in region_ids:
                shp = os.path.join(app_globals.ECOSHP_DIR, id + '.shp')        
                if os.path.exists(shp):
                    ct+=1
                    tmp_xml += """
                            <Layer name="layer_name" srs="+proj=latlong +datum=WGS84">
                            <StyleName>style</StyleName>
                            <Datasource>
                              <Parameter name="type">shape</Parameter>
                              <Parameter name="file">layer_name</Parameter>
                            </Datasource>
                          </Layer>""".replace("layer_name",id)
                    
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
    """
    def ecoregion_Option2(self, method, region_id):
        '''This action returns PNG data with the response header Content-Type 
        set to image/png with a 200 status code. It handles URLs of the form:
        
        http://mol.colorado.edu/ecoregion/region_id/zoom/x/y.png
        
        If a tile isn't found a 404 status is returned.
        '''
        if str(method).lower() == 'tile':
            x = request.GET['x']
            y = request.GET['y']
            z = request.GET['zoom']
            png = os.path.join(app_globals.ECOTILE_DIR, region_id, z, x, y + '.png')        
            if os.path.exists(png):
                logging.info('Returning tile : ' + png)
                response.headers['Content-Type'] = 'image/png'
                response.status = 200
                return open(png, 'rb').read()
            logging.info('Tile not found : ' + png)        
            response.status = 404
            
        elif str(method).lower() == 'tilearea':
            '''This action returns PNG data with the response header Content-Type 
            set to image/png with a 200 status code. It handles URLs of the form:
            
            http://mol.colorado.edu/ecoregion/region_id/zoom/x/y.png
            
            If a tile isn't found a 404 status is returned.
            '''
            lowx = request.GET['lowx']
            lowy = request.GET['lowy']
            highx = request.GET['highx']
            highy = request.GET['highy']
            zoom = int(request.GET['zoom'])
            shp = os.path.join(app_globals.ECOSHP_DIR, region_id + '.shp')        
            if os.path.exists(shp):
                logging.info('Sending tiling job to queue : ' + shp)                
                tmp_xml = open(app_globals.ECO_MAP_XML, 'r').read().replace('layer_name', region_id) 
                mapfile = str(app_globals.ECOSHP_DIR +'/'+ region_id + '.mapfile.xml')
                logging.info('Creating mapfile: %s' % (mapfile))     
                open(mapfile, "w+").write(tmp_xml)
                
                bbox = (float(lowx), float(lowy), float(highx), float(highy))
                logging.info('Tiling %s with bbox: %s' % (region_id,str(bbox)))      
                
                tile_dir =  str(app_globals.ECOTILE_DIR.rstrip('/') + "/" + region_id +"/")
                    
                if not os.path.isdir(tile_dir):
                    os.mkdir(tile_dir)
                    
                GenerateTiles.render_tiles(bbox,
                                           mapfile,
                                           tile_dir,
                                           zoom,
                                           zoom,
                                           "MOL-ECOREGION",
                                           num_threads=app_globals.TILE_QUEUE_THREADS)
                response.status = 200   
                return
            logging.info('Region not found : ' + shp)        
            response.status = 404
    """
