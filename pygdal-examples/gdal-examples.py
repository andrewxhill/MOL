import sys, logging, os, subprocess

nulfp= open("error.log", "a")

###Change the projection of a file to the GMaps projection 900913
p = subprocess.Popen(
    ["gdalwarp",
     "-of",
     "GTiff",
     "-t_srs",
     "epsg:900913",
     infile_name,
     outfile_name)
    ], stderr=nulfp)
p.wait()

#Change a file from one format to another, for example .TIF to .ASC
p = subprocess.Popen(
    ["gdal_translate",
     "-of",
     "AAIGrid",
     infile_name,
     outfile_name)
    ], stderr=nulfp)
p.wait()

#Run Tim R's tiling tool from Python
p = subprocess.Popen(
    ["java",
    "-mx300m",
    "-classpath",
    "/tiler/classes:/tiler/lib/maxent.jar",
    "-Djava.awt.headless=true",
    "raster/GridToGoogle",
    infile_name,
    outdir_name,
    zoom_level
    ], stderr=nulfp)
p.wait()



#####OLD pipeline that reprojects/converts/extracts metadata/tiles####

        p = subprocess.Popen(
            ["gdalwarp",
             "-of",
             "GTiff",
             "-t_srs",
             "epsg:900913",
             os.path.join(tmp_store,filename),
             os.path.join(tmp_store,"out.tif")
            ], stderr=nulfp)
        p.wait()
        p = subprocess.Popen(
            ["gdal_translate",
             "-of",
             "AAIGrid",
             os.path.join(tmp_store,"out.tif"),
             os.path.join(tmp_store,"out.asc")
            ], stderr=nulfp)
        p.wait()
        fname = "out.asc"
    
    
    
    info = open(os.path.join(tmp_tiles,"info.json"),"w+")
    p = subprocess.Popen(
        ["gdalinfo",
         os.path.join(tmp_store,fname)
        ], stdout=subprocess.PIPE).communicate()[0]
    p = p.split("\n")
    info.write('{"tilesetUrl":"http://mol.colorado.edu/tiles/%s/z{z}/{x}/{y}.png", ' % k)
    info.write('"zoomMin": 0, ')
    info.write('"zoomMax": %s, ' % str(ZOOM-1))
    t = p[7].split()
    info.write('"bbox_minx": %s, ' % t[3].replace(",",""))
    info.write('"bbox_maxy": %s, ' % t[4].replace(",","").replace(")",""))
    t = p[10].split()
    info.write('"bbox_maxx": %s, ' % t[3].replace(",",""))
    info.write('"bbox_miny": %s }' % t[4].replace(",","").replace(")",""))
    info.close()
    GS_Upload(os.path.join(tmp_tiles,"info.json"),"%s/info.json" % k)
    
    
    info = open(os.path.join(tmp_tiles,"info.json"),"w+")
    p = subprocess.Popen(
        ["gdalinfo",
         os.path.join(tmp_store,fname)
        ], stdout=subprocess.PIPE).communicate()[0]
    p = p.split("\n")
    info.write('{"tilesetUrl":"http://raster-server-private-tiles.commondatastorage.googleapis.com/%s/z{z}/{x}/{y}.png", ' % k)
    info.write('"zoomMin": 0, ')
    info.write('"zoomMax": %s, ' % str(ZOOM-1))
    t = p[7].split()
    info.write('"bbox_minx": %s, ' % t[3].replace(",",""))
    info.write('"bbox_maxy": %s, ' % t[4].replace(",","").replace(")",""))
    t = p[10].split()
    info.write('"bbox_maxx": %s, ' % t[3].replace(",",""))
    info.write('"bbox_miny": %s }' % t[4].replace(",","").replace(")",""))
    info.close()
    
    
    p = subprocess.Popen(
        ["gdal_translate",
         "-of",
         "PNG",
         os.path.join(tmp_store,fname),
         os.path.join(tmp_tiles+"/","thumb.png")
        ], stderr=nulfp)
    p.wait()
    
    p = subprocess.Popen(
        ["java",
        "-mx300m",
        "-classpath",
        "/tiler/classes:/tiler/lib/maxent.jar",
        "-Djava.awt.headless=true",
        "raster/GridToGoogle",
        os.path.join(tmp_store,fname),
        tmp_tiles,
        str(ZOOM)
        ], stderr=nulfp)
    p.wait()


