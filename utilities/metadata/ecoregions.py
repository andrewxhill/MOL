import ogr, glob, os
import urllib, urllib2
import simplejson, datetime

class NewEcoregion():
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
              "collectionKey": "collection/ecoregions/wwf/1",
              "creationDate": "2001",
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
    eco_code = f.replace('.shp','')
    out = NewEcoregion()
    out.source = "World Wildlife Fund (WWF)"
    out.type = "Ecoregion"
    out.location = "/ftp/ecoregion/shp/%s.shp" % eco_code
    out.format = "Esri Shapefile"
    out.geoFormat = "vector"
    out.geoType = "multipolygon"
    out.newVariable('eco_code', eco_code)
    
    ds = ogr.Open ( f )
    lyr = ds.GetLayerByName( eco_code )
    feat_def = lyr.GetLayerDefn()
    
    region, biome, econum, ecosym, ecoid = None, None, None, None, None
    for feat in lyr:
        if region is None:
            region = feat.GetField('G200_REGIO')
        if biome is None:
            biome = feat.GetField('BIOME')
        if econum is None:
            econum = feat.GetField('ECO_NUM')
        if ecosym is None:
            ecosym = feat.GetField('ECO_SYM')
        if ecoid is None:
            ecoid = feat.GetField('ECO_ID')
    out.newVariable('G200_REGIO', region)
    out.newVariable('BIOME', biome)
    out.newVariable('ECO_NUM', econum)
    out.newVariable('ECO_SYM', ecosym)
    out.newVariable('ECO_ID', ecoid)
            
    out.extentText = region
    feat = lyr.GetFeature(0)
    geom = feat.GetGeometryRef()
    
    out.name = feat.GetField('ECO_NAME')
    
    out.srs = "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"
    extent = lyr.GetExtent()
    out.xmin = extent[0]
    out.ymin = extent[2]
    out.xmax = extent[1]
    out.ymax = extent[3]
    
    return out.json()

def newCollection():
    return {
          "source":"World Wildlife Fund (WWF)",
          "type":"Ecoregion",
          "name":"World Ecoregions",
          "description":"The WWF's Conservation Science Program (CSP) has developed a biogeographic regionalization of the Earth's terrestrial biodiversity. WWF termed the biogeographic units ecoregions, defined as relatively large units of land or water containing distinct assemblages of natural communities sharing a large majority of species, dynamics, and environmental conditions. Ecoregions represent the original distribution of distinct assemblages of species and communities.",
          "url":"http://www.worldwildlife.org/science/ecoregions/item1267.html",
          "agreements":{},
          "creationDate": "2001",
          "uploadDate": str(datetime.datetime.now()),
          "changeDate": "2001",
          "allowed_uses":{
              "visualization": "unknown",
              "download": "unknown",
             },
              "references":{
                 "0":{
                    "authors":"Olson, D.M.; Dinerstein, E.; Wikramanayake, E.; Burgess, N.; Powell, G.; Underwood, E. C.; D'Amico, J.; Itoua, I.; Strand, H.; Morrison, J.; Loucks, C.; Allnutt, T.; Ricketts, T.H.; Kura, Y.; Wettengel, W.; Kassem,K.",
                    "year":2001,
                    "publication":"BioScience, Volume 51, Issue 11, p.933-938",
                    "title":"Terrestrial ecoregions of the world: a new map of life on earth"
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
           "taxa": [
                {"scope": "class",
                 "name": "Mammalia"},
                {"scope": "class",
                 "name": "Reptilia"},
                {"scope": "class",
                 "name": "Amphibia"}
           ]
        }
        
if __name__== '__main__':
    os.chdir("/ftp/ecoregion/shp")
    url = 'http://axh.mol-lab.appspot.com/andrew'
    #url = 'http://localhost:8080/andrew'
    #os.chdir("/home/andrew/Documents")
    values = {'payload' : simplejson.dumps(newCollection()),
              'key_name' : 'collection/ecoregions/wwf/1'}
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    response = urllib2.urlopen(req)
    the_page = response.read()
    
    for f in glob.glob("*.shp"):
        #if f == 'AA0101.shp':
        c = f.replace('.shp', '')
        out = newMetadata(f)
        values = {'payload' : simplejson.dumps(out),
                  'key_name' : 'ecoregion/wwf/%s' % c,
                  'parent_key_name' : 'ecoregion/wwf/%s' % c,
                  'parent_kind' : 'MultiPolygon'}
        try:
            data = urllib.urlencode(values)
            req = urllib2.Request(url, data)
            response = urllib2.urlopen(req)
            the_page = response.read()
        except:
            print c
            
    
    
