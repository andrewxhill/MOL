#!/usr/bin/env python
#
# Copyright 2010 Map Of Life
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

from google.appengine.api import images, memcache as m
from google.appengine.ext import db
from mapreduce import operation as op
from mol.db import *
import cStringIO
import png
import logging
import simplejson

memcache = m.Client()

    
def delete(entity):
    """Deletes the entity from the datastore."""
    #if len(entity.key().name().split('/')[1]) < 6:
    
    yield op.db.Delete(entity)

def clean_term_index(entity):
    """Cleans term indexes of terms pointing to old layers"""
    #if len(entity.key().name().split('/')[1]) < 6:
    if entity.parent() is None:
        yield op.db.Delete(entity)
'''
def set_range_map(entity):
    key_name = entity.key().name()
    if TileSetIndex.get_by_key_name(key_name) is not None:
        entity.hasRangeMap = True
    else:
        entity.hasRangeMap = False
    if not entity.names:
        entity.names = []
        logging.warn('SpeciesIndex(%s) has no names' % key_name)
    yield op.db.Put(entity)

def move_tile_set(entity):
    old_key = entity.key().name()
    name = ' '.join(old_key.split('/')[2].split('_')).capitalize().strip()
    subname = "MOL Range Map"
    new_key = "range/mol/%s" % old_key
    """
    info = {
            "extentNorthWest": str(entity.extentNorthWest),
            "extentSouthEast": str(entity.extentSouthEast),
            "proj": str(entity.proj)
           }
    mpoly = MultiPolygon(
                key_name = new_key,
                info = simplejson.dumps(info),
                name = name,
                subname = subname,
                source = 'MOL',
                category = 'range'
            )
    yield op.db.Put(mpoly)
    """
    taxa = Species.get_by_key_name(old_key)
    cls = simplejson.loads(taxa.classification)
    terms = []
    terms.append(name.lower())
    for a in ["genus","family","order","class","phylum","species","infraspecies","superfamily"]:
        if a in cls:
            if cls[a] not in ["",None,False]:
                if cls[a] not in terms:
                    terms.append(cls[a])
    i = 0
    for t in terms:
        rank = int((len(terms)-i) * 90/(len(terms)))
        mpi = MultiPolygonIndex(
                key_name = str(i),
                parent = db.Key.from_path('MultiPolygon',new_key),
                term = str(t).strip().lower(),
                rank = rank,
              )
        yield op.db.Put(mpi)
        i+=1
'''
def move_index_to_mastersearch(entity):
    #multipoly, done
    ms = MasterSearchIndex(
        key_name = entity.key().name(),
        parent = entity.key().parent(),
        term = entity.term,
        rank = entity.rank )
    yield op.db.Put(ms)


