import ogr, glob, os
import urllib, urllib2
import simplejson, datetime

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
              "collectionKey": "collection/ranges/iucn/1",
              "creationDate": "2008",
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
    taxon = f.replace('.shp','')
    out = NewRange()
    out.taxon = taxon
    out.source = "International Union for Conservation of Nature (IUCN)"
    out.type = "Range"
    out.location = "/ftp/range/shp/animalia/species/%s.shp" % taxon
    out.format = "Esri Shapefile"
    out.geoFormat = "vector"
    out.geoType = "multipolygon"
    
    ds = ogr.Open ( f )
    lyr = ds.GetLayerByName( taxon )
    feat_def = lyr.GetLayerDefn()
    
    presence, origin, seasonal, binomial = None, None, None, None
    for feat in lyr:
        if presence is None:
            presence = feat.GetField('PRESENCE')
        if origin is None:
            origin = feat.GetField('ORIGIN')
        if seasonal is None:
            seasonal = feat.GetField('SEASONAL')
        if binomial is None:
            binomial = feat.GetField('BINOMIAL')
    out.newVariable('PRESENCE', presence)
    out.newVariable('ORIGIN', origin)
    out.newVariable('SEASONAL', seasonal)
    out.newVariable('BINOMIAL', binomial)

    feat = lyr.GetFeature(0)
    geom = feat.GetGeometryRef()
    
    out.name = feat.GetField('BINOMIAL')
    
    out.srs = "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"
    extent = lyr.GetExtent()
    out.xmin = extent[0]
    out.ymin = extent[2]
    out.xmax = extent[1]
    out.ymax = extent[3]
    
    return out.json()

def newCollection():
    return {
          "source":"International Union for Conservation of Nature (IUCN)",
          "type":"Range",
          "name":"Digital Distribution Maps of The IUCN Red List of Threatened Species",
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
           "taxa": [
                {"scope": "class",
                 "name": "Mammalia"},
                {"scope": "class",
                 "name": "Amphibia"},
                {"scope": "class",
                 "name": "Reptilia"}
           ]
        }
        
if __name__== '__main__':
    os.chdir("/shp/animalia/species/")
#    os.chdir("/Users/tuco/Data/MoL/mol-data/range/shp/animalia/species/")
    url = 'http://axh.mol-lab.appspot.com/andrew'
    #url = 'http://localhost:8080/andrew'
    #os.chdir("/home/andrew/Documents")
    values = {'payload' : simplejson.dumps(newCollection()),
              'key_name' : 'collection/ranges/iucn/1'}
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    response = urllib2.urlopen(req)
    the_page = response.read()
    
    for f in glob.glob("*.shp"):
        c = f.replace('.shp', '')
        out = newMetadata(f)
        values = {'payload' : simplejson.dumps(out),
                  'key_name' : 'range/iucn/%s' % c,
                  'parent_key_name' : 'range/iucn/%s' % c,
                  'parent_kind' : 'MultiPolygon'}
        try:
            data = urllib.urlencode(values)
            req = urllib2.Request(url, data)
            print 'File %s metadata: %s' % (c, values)
            response = urllib2.urlopen(req)
            the_page = response.read()
        except:
            print c
