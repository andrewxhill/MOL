from math import pi, sin, log, exp, atan
import mapnik
import ogr
import logging
import os
import shutil
import threading

DEG_TO_RAD = pi / 180
RAD_TO_DEG = 180 / pi

def minmax (a, b, c):
    a = max(a, b)
    a = min(a, c)
    return a

class GoogleProjection:
    def __init__(self, levels=18):
        self.Bc = []
        self.Cc = []
        self.zc = []
        self.Ac = []
        c = 256
        for d in range(0, levels):
            e = c / 2;
            self.Bc.append(c / 360.0)
            self.Cc.append(c / (2 * pi))
            self.zc.append((e, e))
            self.Ac.append(c)
            c *= 2

    def fromLLtoPixel(self, ll, zoom):
        d = self.zc[zoom]
        e = round(d[0] + ll[0] * self.Bc[zoom])
        f = minmax(sin(DEG_TO_RAD * ll[1]), -0.9999, 0.9999)
        g = round(d[1] + 0.5 * log((1 + f) / (1 - f)) * -self.Cc[zoom])
        return (e, g)

    def fromPixelToLL(self, px, zoom):
        e = self.zc[zoom]
        f = (px[0] - e[0]) / self.Bc[zoom]
        g = (px[1] - e[1]) / -self.Cc[zoom]
        h = RAD_TO_DEG * (2 * atan(exp(g)) - 0.5 * pi)
        return (f, h)



class RenderThread:
    #def __init__(self, , shpfile, proj, w, h, params):
    def __init__(self, tile_dir, shpfile, proj, z, params):
        self.m = mapnik.Map(256, 256)
        self.m.background = mapnik.Color(params.get('background'))
        
        s = mapnik.Style()
        r=mapnik.Rule()
        r.symbols.append(mapnik.PolygonSymbolizer(mapnik.Color(params.get('polygon'))))
        r.symbols.append(mapnik.LineSymbolizer(mapnik.Color(params.get('line')),params.get('line-width')))
        s.rules.append(r)
        self.m.append_style('My Style',s)

        self.lyr = mapnik.Layer('world',proj)
        self.lyr.datasource = mapnik.Shapefile(file=str(shpfile))
        self.lyr.styles.append('My Style')
        self.m.layers.append(self.lyr)
        
        self.prj = mapnik.Projection(self.m.srs)
        self.tileproj = GoogleProjection(z + 1)
        

    def render_tile(self, tile_uri, x, y, z):
        # Calculate pixel positions of bottom-left & top-right
        p0 = (x * 256, (y + 1) * 256)
        p1 = ((x + 1) * 256, y * 256)

        # Convert to LatLong (EPSG:4326)
        l0 = self.tileproj.fromPixelToLL(p0, z);
        l1 = self.tileproj.fromPixelToLL(p1, z);

        # Convert to map projection (e.g. mercator co-ords EPSG:900913)
        c0 = self.prj.forward(mapnik.Coord(l0[0], l0[1]))
        c1 = self.prj.forward(mapnik.Coord(l1[0], l1[1]))

        # Bounding box for the tile
        if hasattr(mapnik, 'mapnik_version') and mapnik.mapnik_version() >= 800:
            bbox = mapnik.Box2d(c0.x, c0.y, c1.x, c1.y)
        else:
            bbox = mapnik.Envelope(c0.x, c0.y, c1.x, c1.y)
        render_size = 256
        self.m.resize(render_size, render_size)
        self.m.zoom_to_box(bbox)
        self.m.buffer_size = 128

        # Render image with default Agg renderer
        im = mapnik.Image(render_size, render_size)
        mapnik.render(self.m, im)
        im.save(tile_uri, 'png')

def render(tile_dir, shpfile, x, y, z, params, proj, overwrite=False, empty_bytes=334):  
    # Launch rendering threads
    renderer = RenderThread(tile_dir, shpfile, proj, z, params)      
    # check if we have directories in place
    zoom = "%s" % z
    
    if (x < 0) or (x >= 2 ** z):
        return
        # check if we have directories in place
    str_x = "%s" % x
    
    if (y < 0) or (y >= 2 ** z):
        return
    str_y = "%s" % y
    tile_uri = str(os.path.join(tile_dir , zoom , str_x , str_y + '.png'))  
    null_uri = str(os.path.join(tile_dir , zoom , str_x , str_y + '.null'))
    
    tile_path = str(os.path.join(tile_dir, zoom , str_x))
    if not os.path.isdir(tile_path):
        os.makedirs(tile_path)
        
    #skip existing tiles 
    if overwrite:
        try:
            os.remove(tile_uri)
        except:
            pass
    
    renderer.render_tile(tile_uri, x, y, z)
    bytes = os.stat(tile_uri)[6]
    empty = ''
    if bytes == empty_bytes:
        empty = " Empty Tile "
        #remove the png
        os.remove(tile_uri)
        #create an empty file placeholder
        open(tile_uri.replace('.png','.null'), "w+").close()
        return 204
    else:
        return True
