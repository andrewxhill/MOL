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



class OVRenderThread:
    def __init__(self, tile_dir, shpfile, proj, w, h, params):
        self.tile_dir = tile_dir
        self.m = mapnik.Map(w, h)
        self.m.background = mapnik.Color(params.get('background'))
        s = mapnik.Style()
        r=mapnik.Rule()
        r.symbols.append(mapnik.PolygonSymbolizer(mapnik.Color(params.get('polygon'))))
        r.symbols.append(mapnik.LineSymbolizer(mapnik.Color(params.get('line')),params.get('line-width')))
        s.rules.append(r)
        self.m.append_style('My Style',s)
        self.lyr = mapnik.Layer('world',proj)
        self.lyr.datasource = mapnik.Shapefile(file=shpfile)
        self.lyr.styles.append('My Style')
        self.m.layers.append(self.lyr)
        
        # Load style XML
       #mapnik.load_map(self.m, mapfile, True)
        # Obtain <Map> projection
        self.prj = mapnik.Projection(self.m.srs)
        # Projects between tile pixel co-ordinates and LatLong (EPSG:4326)


    def render_tile(self, tile_uri, w, h):
        
        self.m.resize(w, h)
        
        #self.m.zoom_to_box(self.lyr.envelope())
        bb = (self.lyr.envelope().minx,self.lyr.envelope().miny,self.lyr.envelope().maxx,self.lyr.envelope().maxy)
        lW = bb[2] - bb[0]
        lH = bb[3] - bb[1]
        lR = lW/lH
        r = w/h
        
        mW = 0
        mH = 0
        if lR > r:
            mH = (lW * h)/(w * lH)
        elif r < lR:
            mW = (w * lH) / (lW * h)
        
        x1 = bb[0] - 0.5*mW
        x2 = bb[2] + 0.5*mW
        
        y1 = bb[1] - 0.5*mH
        y2 = bb[3] + 0.5*mH
        
        c0 = self.prj.forward(mapnik.Coord(x1, y1))
        c1 = self.prj.forward(mapnik.Coord(x2,y2))

        # Bounding box for the tile
        if hasattr(mapnik, 'mapnik_version') and mapnik.mapnik_version() >= 800:
            bb = mapnik.Box2d(c0.x, c0.y, c1.x, c1.y)
        else:
            bb = mapnik.Envelope(c0.x, c0.y, c1.x, c1.y)
        self.m.zoom_to_box(bb)
        
        self.m.buffer_size = 128

        # Render image with default Agg renderer
        im = mapnik.Image(w, h)
        mapnik.render(self.m, im)
        im.save(tile_uri, 'png')

def render(id, tile_dir, shpfile, proj, w, h):  
    # Launch rendering threads
    renderer = OVRenderThread(tile_dir, shpfile, proj, w, h)      
    
    tile_uri = str(os.path.join(tile_dir , id+'.png'))  
    
    renderer.render_tile(tile_uri, w, h)
