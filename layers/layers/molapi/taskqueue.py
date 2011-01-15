import sys, logging, os, shutil, datetime, time, shlex, subprocess
import StringIO

class Layer():
    zoom = 5 #sets the maximum zoom we want to process
    info = {}
    errors = []
    converted = False
    tiled = False
    tileDir = "tiles/" #/some/tmp/folder/for/tiles/
    ascDir = "" #/some/tmp/folder/for/asc/
    
    
    def __init__(self, dirname="",filename=None):
        """raster: string filename of file to process"""
        if filename is not None:
            self.origRaster = dirname.rstrip("/") + "/" + filename if dirname != "" else filename
            self.id = filename.split('.')[0]
            self.verifyId()
            self.tileFolder = self.tileDir + self.id
            self.ascName = self.ascDir + "%s.asc" % self.id
            self.nulfp= open('%s.log' % self.id,'w')
        
    def verifyId(self):
        """check to see that the id exists on GAE"""
        return True
    
    def getInfo(self,fn):
        #use gdalinfo to populate an info object
        info = subprocess.Popen(
            ["gdalinfo",
             fn
            ], stdout=subprocess.PIPE).communicate()[0]
        #better parsing needed
        """
        info = info.split("\n")
        self.info["id"] = self.id
        self.info["zoom"] = {}
        self.info["box"] = {}
        
        self.info["zoom"]["min"] = 0
        self.info["zoom"]["max"] = self.zoom
        
        upper = info[7].split()
        lower = info[10].split()
        self.info["box"]["xmin"] = upper[3].replace(",","")
        self.info["box"]["xmax"] = lower[3].replace(",","")
        self.info["box"]["ymax"] = upper[3].replace(",","").replace(")","")
        self.info["box"]["ymin"] = lower[3].replace(",","").replace(")","")
        """
        #should grab projection info here also
        
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
            "/tiler/classes:/tiler/lib/maxent.jar",
            "-Djava.awt.headless=true",
            "raster/GridToGoogle",
            self.ascName,
            self.tileFolder,
            str(self.zoom+1)
            ], stderr=self.nulfp)
        self.tiling.wait()
        
    def registerMetadata(self):
        #send metadata to GAE
        return True
        
    def storeTiles(self):
        #store tiles in couchdb
        return True
        
if __name__ == "__main__":
    #run the code
    filename = str(sys.argv[1])
    try:
        dirname = str(sys.argv[2])
    except:
        dirname = ""
        
    layer = Layer(dirname=dirname,filename=filename)
    #layer.projectToGMAP()
    layer.convertToASC()
    layer.tile()
