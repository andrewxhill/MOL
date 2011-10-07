#!/usr/bin/env python

# Copyright 2011 Aaron Steele
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import glob
from optparse import OptionParser
import os
from osgeo import osr
import shlex
import subprocess
import yaml

def _getoptions():
    ''' Parses command line options and returns them.'''
    parser = OptionParser()
    parser.add_option('--dir', 
                      type='string', 
                      dest='dir',
                      metavar='DIR', 
                      help='Directory of shapefiles')
    parser.add_option('-p', '--prepare_only', 
                      action="store_true", 
                      dest='prepare_only',
                      help='Creates tables only.')                          
    parser.add_option('-t', '--data-type', 
                      type='string', 
                      dest='data_type',
                      help='Data type (ranges|ecoregions|protectedareas')
    return parser.parse_args()[0]

if __name__ == '__main__':
    options = _getoptions()
    os.chdir(options.dir)
    for f in glob.glob('*.shp'):
        sql_file = open('%s.sql' % f, 'wr+')
        proj = open('%s.prj' % os.path.splitext(f)[0], 'r').read()
        srs = osr.SpatialReference()
        srs.ImportFromESRI([proj])
        srs.AutoIdentifyEPSG()
        srid = srs.GetAuthorityCode(None)
        print 'SRID=%s' % srid
        if srid == None:
            print 'SRID -1, setting to 3857'
            srid = 3857
        if options.prepare_only:
            command = 'shp2pgsql -I -p -s %s %s public.%s > %s.sql' % (srid, f, options.data_type, sql_file.name)
        else:
            command = 'shp2pgsql -a -s %s %s public.%s > %s.sql' % (srid, f, options.data_type, sql_file.name)
        args = shlex.split(command)
        subprocess.call(args, stdout=sql_file)
        sql_file.seek(0)
        if not options.prepare_only:
            sql_mods = """
COMMIT;
update %s set the_geom_webmercator = ST_Transform(the_geom, 3857);""" % options.data_type
        else:
            sql_mods = """ 
COMMIT;
select AddGeometryColumn('%s', 'the_geom_webmercator', 3857, 'MULTIPOLYGON', 2);
""" % options.data_type
        content = sql_file.read()
        content = content.replace('COMMIT;', sql_mods)
        sql_file.truncate(0)
        sql_file.write(content)
        sql_file.flush()
        sql_file.close()
        command = 'psql -U postgres -d mol -f %s' % sql_file.name
        args = shlex.split(command)
        subprocess.call(args)
        if options.prepare_only:
            break

