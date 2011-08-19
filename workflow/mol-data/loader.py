#!/usr/bin/env python
#
# Copyright 2011 Aaron Steele
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""This script implements the MoL workflow process for layers."""

import copy
import csv
import glob
import logging
from optparse import OptionParser
import os
import simplejson
import shlex
import subprocess
import sys
import yaml

class Config(object):
    """Wraps the YAML object for a MoL config.yaml object."""
    
    @classmethod
    def lower_keys(cls, x):
        """Lower cases all nested dictionary keys."""
        if isinstance(x, list):
            return [cls.lower_keys(v) for v in x]
        if isinstance(x, dict):
            return dict((k.lower(), cls.lower_keys(v)) for k, v in x.iteritems())
        return x
    
    class Collection(object):
        def __init__(self, collection):
            self.collection = collection
        
        def get_row(self):
            row = {}
            for k,v in self.collection['required'].iteritems():
                row[k] = v
            for k,v in self.collection['optional'].iteritems():
                if k in ['taxonomy', 'basemaps']:
                    v = simplejson.dumps(v)                        
                row[k] = v
            return row
            
        def get_columns(self):
            cols = []
            cols.extend(self.collection['required'].keys())
            cols.extend(self.collection['optional'].keys())
            cols.extend(self.collection['dbfmapping']['required'].keys())
            cols.extend(self.collection['dbfmapping']['optional'].keys())
            cols.extend(['layer_source', 'layer_collection', 'layer_filename', 'layer_polygons'])
            return cols

        def get_mapping(self, required=True):
            """Returns a reverse dbfmapping for convienience."""
            if required:
                mapping = self.collection['dbfmapping']['required'] 
            else:
                mapping = self.collection['dbfmapping']['optional'] 
            return dict((source, mol) for mol,source in mapping.iteritems())
            
        def getdir(self):
            return self.collection['directoryname']

        def get(self, key, default=None):
            return self.collection.get(key, default)
        
    def __init__(self, filename):
        self.config = Config.lower_keys(yaml.load(open(filename, 'r').read()))

    def collection_names(self):
        return [x.get('directoryname') for x in self.collections()]

    def collections(self):
        for collection in self.config['collections']:
            yield Config.Collection(collection)

def _getoptions():
    ''' Parses command line options and returns them.'''
    parser = OptionParser()
    parser.add_option('--config_file', 
                      type='string', 
                      dest='config_file',
                      metavar='FILE', 
                      help='Bulkload YAML config file.')    
    parser.add_option('-d', '--dry_run', 
                      action="store_true", 
                      dest='dry_run',
                      help='Creates CSV file but does not bulkload it')                          
    parser.add_option('-l', '--localhost', 
                      action="store_true", 
                      dest='localhost',
                      help='Shortcut for bulkloading to http://localhost:8080/_ah/remote_api')                          
    parser.add_option('--url', 
                      type='string', 
                      dest='url',
                      help='URL endpoint to /remote_api to bulkload to.')                          
    return parser.parse_args()[0]

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    options = _getoptions()

    source_dirs = [x for x in os.listdir('.') if os.path.isdir(x)]
    if options.dry_run:
            logging.info('Performing a dry run...')
    logging.info('Processing source directories: %s' % source_dirs)

    for sd in source_dirs: # For each source dir (e.g., jetz, iucn)
        os.chdir(sd)
        config = Config('config.yaml')        
        logging.info('Collections in %s: %s' % (sd, config.collection_names()))

        for collection in config.collections(): # For each collection dir in the source dir       
            coll_dir = collection.getdir()
            os.chdir(coll_dir)
            
            # Create collection.csv writer
            coll_file = open('collection.csv.txt', 'w')
            coll_cols = collection.get_columns()
            coll_cols.sort()
            coll_csv = csv.DictWriter(coll_file, coll_cols)
            coll_csv.writer.writerow(coll_csv.fieldnames)
            coll_row = collection.get_row()
            coll_row['layer_source'] = sd
            coll_row['layer_collection'] = coll_dir            
            
            # Create polygons.csv writer
            poly_file = open('collection.polygons.csv.txt', 'w')
            poly_dw = csv.DictWriter(poly_file, ['shapefilename', 'json'])
            poly_dw.writeheader()

            # Convert DBF to CSV and add to collection.csv
            shpfiles = glob.glob('*.shp')
            logging.info('Processing %d layers in the %s collection' % (len(shpfiles), coll_dir))
            for sf in shpfiles:
                logging.info('Extracting DBF fields from %s' % sf)
                csvfile = '%s.csv' % sf
                if os.path.exists(csvfile): # ogr2ogr barfs if there are *any* csv files in the dir
                    os.remove(csvfile)
                command = 'ogr2ogr -f CSV "%s" "%s"' % (csvfile, sf)
                args = shlex.split(command)
                subprocess.call(args)
                
                # Copy and update coll_row with DBF fields
                row = copy.copy(coll_row)                
                row['layer_filename'] = os.path.splitext(sf)[0]
                dr = csv.DictReader(open(csvfile, 'r'), skipinitialspace=True)
               
                layer_polygons = []
                
                for dbf in dr: # For each row in the DBF CSV file (1 row per polygon)

                    polygon = {}

                    for source, mol in collection.get_mapping().iteritems(): # Required DBF fields
                        sourceval = dbf.get(source)
                        if not sourceval:
                            logging.error('Missing required DBF field %s' % mol)
                            sys.exit(1)        
                        row[mol] = sourceval
                        polygon[mol] = sourceval

                    for source, mol in collection.get_mapping(required=False).iteritems(): #Optional DBF fields
                        sourceval = dbf.get(source)
                        if not sourceval:
                            continue
                        row[mol] = sourceval
                        polygon[mol] = sourceval

                    # Write coll_row to collection.csv
                    coll_csv.writerow(row)

                    layer_polygons.append(polygon)

                # Create JSON representation of dbfjson
                polygons_json = simplejson.dumps(layer_polygons) # TODO: Showing up as string instead of JSON in API
                poly_dw.writerow(dict(shapefilename=row['layer_filename'], json=polygons_json))
                poly_file.flush()
                poly_file.close()
                
                
            # Important: Close the DictWriter file before trying to bulkload it
            logging.info('All collection metadata saved to %s' % coll_file.name)
            coll_file.flush()
            coll_file.close()
            
            if options.dry_run:
                logging.info('Dry run complete!')
                sys.exit(1)
                
            os.chdir('../../')
            filename = os.path.abspath('%s/%s/collection.csv.txt' % (sd, coll_dir))
            config_file = os.path.abspath(options.config_file)

            if options.localhost:
                options.url = 'http://localhost:8080/_ah/remote_api'

            # Bulkload Layer entities to App Engine for entire collection
            cmd = "appcfg.py upload_data --config_file=%s --filename=%s --kind=%s --url=%s" 
            cmdline = cmd % (config_file, filename, 'Layer', options.url)
            args = shlex.split(cmdline)
            #logging.info(cmdline)
            subprocess.call(args)
            
            # Bulkload LayerIndex entities to App Engine for entire collection
            cmd = "appcfg.py upload_data --config_file=%s --filename=%s --kind=%s --url=%s" 
            cmdline = cmd % (config_file, filename, 'LayerIndex', options.url)
            args = shlex.split(cmdline)
            #logging.info(cmdline)
            subprocess.call(args)
            
            logging.info('Loading finished!')
                
