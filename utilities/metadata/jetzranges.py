#!/usr/bin/env python

import ogr
import glob
import os
import urllib, urllib2
import math
import simplejson, datetime
import logging
from optparse import OptionParser

class NewRange():
    def __init__(self):
        self.taxon = None
        self.source = None
        self.type = None
        self.name = None
        self.description = None
        self.extentText = None
        self.srs = None
        self.xmin = None
        self.ymin = None
        self.xmax = None
        self.ymax = None
        self.location = None
        self.format = None
        self.geoFormat = None
        self.geoType = None
        self.resType = None
        self.resUnit = None
        self.resVal = None
        self.variables = []
        
    def newVariable(self, name, value):
        self.variables.append({
                            "name": name,
                            "value": value })
    def json(self):
        return  {
              "taxon": self.taxon,
              "source": self.source,
              "type": self.type,
              "name": self.name,
              "description": self.description,
              "collectionKey": "collection/ranges/jetz/1",
              "creationDate": "2011",
              "storage":{
                 "location": self.location,
                 "format": self.format,
                 "uploadDate": str(datetime.datetime.now()),
              },
              "temporal": {
                    "coverage": {
                        "start": None,
                        "end": None
                    }
              },
              "spatial":{
                 "crs":{
                    "srs": self.srs,
                    "extent":{
                       "text":self.extentText,
                       "coordinates":{
                          "0": self.xmin,
                          "1": self.ymin,
                          "2": self.xmax,
                          "3": self.ymax
                       }
                    },
                    "format": self.geoFormat,
                    "type": self.geoType,
                    "info": {
                       "resolution":{
                          "type": self.resType,
                          "value": self.resVal,
                          "unit": self.resUnit
                       },
                    }
                 }
              },
              "variables": self.variables
            }

class MultiPolygonIndex():
    def __init__(self):
        self.term = None
        self.rank = None

    def json(self):
        return  {
              "term": self.term,
              "rank": self.rank
            }

def newMultiPolygonIndex(taxon):
    mpi = MultiPolygonIndex()
    mpi.term = taxon.lower()
    mpi.rank = 90
    return mpi

class Info():
    def __init__(self):
        self.extentnorthwest = None
        self.extentsoutheast = None
        self.proj = None

    def json(self):
        return  {
              "extentNorthWest": self.extentnorthwest,
              "proj": self.proj,
              "extentSouthEast": self.extentsoutheast
            }

class MultiPolygon():
    def __init__(self):
        self.name = None
        self.subname = 'Jetz Range Map'
        self.source = 'Jetz'
        self.category = 'range'
        self.info = None
# TODO: Check that this gets created automatically in the datastore.
#        self.dateCreated = None 
    def json(self):
        return  {
              "name": self.name,
              "subname": self.subname,
              "source": self.source,
              "category": self.category,
              "info": self.info              
            }

def getTaxon(f):
    ds = ogr.Open ( f )
    lyr = ds.GetLayerByName( f.replace('.shp','') )
    feat_def = lyr.GetLayerDefn()
    feat = lyr.GetFeature(0)
    return feat.GetField('Latin')

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

def newMultiPolygon(f):
    ds = ogr.Open ( f )
    lyr = ds.GetLayerByName( f.replace('.shp','') )
    feat_def = lyr.GetLayerDefn()
    feat = lyr.GetFeature(0)
    mp = MultiPolygon()
    mp.name = feat.GetField('Latin')
    geom = feat.GetGeometryRef()
    extent = MetersToLatLon(lyr.GetExtent())    
    xmin = extent[0]
    ymin = extent[2]
    xmax = extent[1]
    ymax = extent[3]
    info = Info()
    info.extentnorthwest = '%s,%s' % (ymax,xmin)
    info.extentsoutheast = '%s,%s' % (ymin,xmax)
    info.proj = "EPSG:900913"
    mp.info = simplejson.dumps(info.json())
    return mp

def newMasterSearchIndex(taxon):
    msi = MasterSearchIndex()
    msi.term = taxon.lower()
    msi.rank = 90
    return msi

class MasterSearchIndex():
    def __init__(self):
        self.term = None
        self.rank = None

    def json(self):
        return  {
              "term": self.term,
              "rank": self.rank
            }

def newMetadata(f):
    taxon = f.replace('.shp','')
    out = NewRange()
    out.taxon = taxon
    out.source = "Jetz Lab"
    out.type = "Range"
    out.location = "/ftp/range/shp/animalia/species/%s.shp" % taxon
    out.format = "Esri Shapefile"
    out.geoFormat = "vector"
    out.geoType = "multipolygon"
    
    ds = ogr.Open ( f )
    lyr = ds.GetLayerByName( taxon )
    feat_def = lyr.GetLayerDefn()
    
    editsinfo, citation, occ_code, latin = None, None, None, None
    for feat in lyr:
        if editsinfo is None:
            editsinfo = feat.GetField('EditsInfo')
        if citation is None:
            citation = feat.GetField('Citation')
        if occ_code is None:
            occ_code = feat.GetField('OccCode')
        if latin is None:
            latin = feat.GetField('Latin')
    out.newVariable('EditsInfo', editsinfo)
    out.newVariable('Citation', citation)
    out.newVariable('OccCode', occ_code)
    out.newVariable('Latin', latin)

    feat = lyr.GetFeature(0)
    geom = feat.GetGeometryRef()
    
    out.name = feat.GetField('Latin')
    
    out.srs = "+proj=merc +lon_0=0 +k=1 +x_0=0 +y_0=0 +a=6378137 +b=6378137 +units=m +no_defs"
    extent = lyr.GetExtent()
    out.xmin = extent[0]
    out.ymin = extent[2]
    out.xmax = extent[1]
    out.ymax = extent[3]
    
    return out.json()

def newCollection():
    return {
          "source":"Walter Jetz Lab",
          "type":"Range",
          "name":"Digital Distribution Maps of Birds",
          "description":"This dataset contains distribution information of species assessed for The IUCN Red List of Threatened Species. The maps are developed as part of a comprehensive assessment of global biodiversity in order to highlight taxa threatened with extinction, and thereby promote their conservation.",
          "url":"http://www.iucnredlist.org/spatial-data/2010.4/GISData/RLSpatial_metadata_Oct2010.pdf",
          "agreements":{},
          "creationDate": "2009-11",
          "uploadDate": str(datetime.datetime.now()),
          "changeDate": "2010-10",
          "allowed_uses":{
              "visualization": "unknown",
              "download": "unknown",
             },
             "spatial":{
                "crs":{
                   "srs": "+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext +over +no_defs",
                   "extent":{
                      "text":"Global",
                      "coordinates":{
                         "0": -90.0,
                         "1": -180.0,
                         "2": 90.0,
                         "3": 180.0
                      }
                   },
                   "format": "vector",
                   "type": "multipolygon",
                   "info": {
                        "resolution": {
                            "type": None,
                            "value": None,
                            "unit": None
                        }
                    },
                },
            },
           "taxa": [
                {"scope": "class",
                 "name": "Aves"}
           ]
        }

def _getoptions():
    """Parses command line options and returns them."""
    parser = OptionParser()
    parser.add_option("-c", "--command", dest="command",
                      help="Jetz Range command",
                      default=None)
    parser.add_option("-d", "--data-dir", dest="datadir",
                      help="Data directory",
                      default=None)
    parser.add_option("-u", "--url", dest="url",
                      help="URL to load to",
                      default='http://localhost:8080/metadataloader')
    parser.add_option("-r", "--rename", dest="rename",
                      help="Rename the shape files",
                      default='True')
    return parser.parse_args()[0]

def main():
    logging.basicConfig(level=logging.DEBUG)
    options = _getoptions()
    command = options.command.lower()


    logging.info('COMMAND %s' % command)

    if options.datadir == None:
        logging.info('No data directory to process. Aborting.')
        return
    if options.url == None:
        logging.info('No URL to load to. Aborting.')
        return

    os.chdir(options.datadir)
    url = options.url

#    i=0
    if command=='loadindexes':
        for f in glob.glob("*.shp"):
            c=f.replace('.shp','')
            taxon = c.replace('_',' ')
            values = dict(
                key_name='range/jetz/animalia/species/%s' % c,
                taxon=taxon
                )
            try:
                data = urllib.urlencode(values)
                req = urllib2.Request(url, data)
                response = urllib2.urlopen(req)
                the_page = response.read()
#                i+=1
#                print '%s: %s indexes loaded.' % (i,taxon)
            except Exception as e:
                print str(e)
                print 'Indexes for %s failed to load.' % taxon
        return

    if command=='renamefiles':
        for f in glob.glob("*.shp"):
            taxon = getTaxon(f)
            # turn Parus major into parus_major
            fromfile = os.path.join(options.datadir, f.replace('.shp','') )
            tofile = os.path.join(options.datadir, '_'.join(taxon.lower().split(' ')))
            os.rename('%s.dbf' % fromfile, '%s.dbf' % tofile)
            os.rename('%s.prj' % fromfile, '%s.prj' % tofile)
            os.rename('%s.sbn' % fromfile, '%s.sbn' % tofile)
            os.rename('%s.sbx' % fromfile, '%s.sbx' % tofile)
            os.rename('%s.shp' % fromfile, '%s.shp' % tofile)
            os.rename('%s.shx' % fromfile, '%s.shx' % tofile)
            os.rename('%s.shp.xml' % fromfile, '%s.mapfile.xml' % tofile)            
        return
    
    if command=='loadmetadata':
        logging.info('Loading Collection metadata.')
        values = dict(
            payload=simplejson.dumps(newCollection()),
            key_name='collection/range/jetz/latest')
        data = urllib.urlencode(values)
        req = urllib2.Request(url, data)
        response = urllib2.urlopen(req)
        the_page = response.read()
        return

    if command=='loadentities':
        logging.info('Loading entities (MD, MP, MSI, MPI) from directory %s to %s.' % (options.datadir, options.url))        
    #    i=0
        for f in glob.glob("*.shp"):
            taxon = getTaxon(f)
            # turn Parus major into parus_major
            c = '_'.join(taxon.lower().split(' '))
            md = newMetadata(f)
            mp = newMultiPolygon(f)
            mpi = newMultiPolygonIndex(taxon)
            msi = newMasterSearchIndex(taxon)
            values = dict(
                mdpayload=simplejson.dumps(md),
                name=mp.name,
                subname=mp.subname,
                source=mp.source,
                info=mp.info,
                category=mp.category,
                key_name='range/jetz/animalia/species/%s' % c,
                parent_key_name='range/jetz/animalia/species/%s' % c,
                term=taxon
                )
    
            try:
                data = urllib.urlencode(values)
                req = urllib2.Request(url, data)
                response = urllib2.urlopen(req)
                the_page = response.read()
    #            i+=1
    #            print '%s: %s loaded.' % (i,taxon)
            except:
                print 'Entities for %s failed to load.' % taxon
        return

if __name__ == "__main__":
    main()
