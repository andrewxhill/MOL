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
