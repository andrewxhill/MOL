#!/usr/bin/env python

import ogr
import glob
import os
import urllib, urllib2
import simplejson, datetime
import logging
from optparse import OptionParser

class NewProtectedArea():
    def __init__(self):
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
              "source": self.source,
              "type": self.type,
              "name": self.name,
              "description": self.description,
              "collectionKey": "collection/protectedareas/wdpa/1",
              "creationDate": "2010",
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

def newMetadata(f):
    wdpaid = f.replace('.shp','')
    out = NewProtectedArea()
    out.source = "IUCN and UNEP"
    out.type = "Protected Area"
    out.location = "/ftp/pa/shp/%s.shp" % wdpaid
    out.format = "Esri Shapefile"
    out.geoFormat = "vector"
    out.geoType = "multipolygon"
    out.newVariable('wdpaid', wdpaid)
    
    ds = ogr.Open ( f )
    lyr = ds.GetLayerByName( wdpaid )
    feat_def = lyr.GetLayerDefn()
    
    name, country, category, designation, govn_type, marine = None, None, None, None, None, None
    for feat in lyr:
        if name is None:
            name = feat.GetField('NAME_ENG')
        if country is None:
            country = feat.GetField('COUNTRY')
        if category is None:
            category = feat.GetField('IUCNCAT')
        if designation is None:
            designation = feat.GetField('DESIG_ENG')
        if govn_type is None:
            govn_type = feat.GetField('GOVN_TYPE')
        if marine is None:
            marine = feat.GetField('MARINE_C')
    out.newVariable('NAME', name)
    out.newVariable('COUNTRY', country)
    out.newVariable('IUCNCAT', category)
    out.newVariable('MARINE', marine)
            
    out.extentText = country
    feat = lyr.GetFeature(0)
    geom = feat.GetGeometryRef()
    
    out.name = feat.GetField('NAME_ENG    ')
    
    out.srs = "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"
    extent = lyr.GetExtent()
    out.xmin = extent[0]
    out.ymin = extent[2]
    out.xmax = extent[1]
    out.ymax = extent[3]
    
    return out.json()

def newCollection():
    return {
          "source":"IUCN and UNEP",
          "type":"Ecoregion",
          "name":"World Database on Protected Areas",
          "description":"An interactive database for protected areas worldwide, reconciling governmental, expert and general public opinions on protected areas. It encompasses the World Database on Protected Areas and provides a platform for the protected area constituency.",
          "url":"http://www.protectedplanet.net/about",
          "agreements":{},
          "creationDate": "2010",
          "uploadDate": str(datetime.datetime.now()),
          "changeDate": "2010",
          "allowed_uses":{
              "visualization": "unknown",
              "download": "unknown",
             },
              "references":{
                 "0":{
                    "authors":"IUCN and UNEP",
                    "year":2010,
                    "publication":"UNEP-WCMC. Cambridge, UK. www.protectedplanet.net",
                    "title":"The World Database on Protected Areas (WDPA)"
                    }
                 },
             "spatial":{
                "crs":{
                   "srs": "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs",
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
        }
        
def _getoptions():
    """Parses command line options and returns them."""
    parser = OptionParser()
    parser.add_option("-d", "--data-dir", dest="datadir",
                      help="Data directory",
                      default=None)
    parser.add_option("-u", "--url", dest="url",
                      help="URL to load to",
                      default='http://localhost:8080/metadataloader')
    return parser.parse_args()[0]

if __name__== '__main__':
#    os.chdir("/ftp/pa/shp")
#    url = 'http://axh.mol-lab.appspot.com/andrew'
    logging.basicConfig(level=logging.DEBUG)
    options = _getoptions()    
    logging.info('Working directory: %s' %options.datadir)
    logging.info('URL: %s' %options.url)
    os.chdir(options.datadir)
    url = options.url
    values = dict(
        payload=simplejson.dumps(newCollection()),
        key_name='collection/protectedareas/wdpa/1')
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    response = urllib2.urlopen(req)
    the_page = response.read()
    
    for f in glob.glob("*.shp"):
        c = f.replace('.shp', '')
        out = newMetadata(f)
        values = dict(
            payload=simplejson.dumps(out),
            key_name='protectedareas/wdpa/%s' % c,
            parent_key_name='protectedareas/wdpa/%s' % c,
            parent_kind='MultiPolygon')
        try:
            data = urllib.urlencode(values)
            req = urllib2.Request(url, data)
            response = urllib2.urlopen(req)
            the_page = response.read()
        except:
            print c
