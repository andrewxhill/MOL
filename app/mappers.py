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
import math
import png
import logging
import simplejson
from mapreduce import operation as op

memcache = m.Client()

def explode(str):
    if str is None:
        return []
    return [x.strip().lower() for x in str.split()]

def delete_metadata_index(entity):
    yield op.db.Delete(entity)

def report_duplicate_msi(entity):
    """Reports duplicate MasterSearchIndex entities."""
    if not entity.parent():
        yield op.counters.Increment('NOPARENT-%s' % entity.term)
        return
    for dup in db.Query(MasterSearchIndex).filter('term', entity.term).ancestor(entity.parent()):
        if dup.key() != entity.key():
            yield op.counters.Increment(entity.term)

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

def fix_extents(entity):
    """
    info = {"extentNorthWest": "lat=22.8249480851,lng=-84.0751669713", "proj": "EPSG:900913", "extentSouthEast": "22.4087368727,-83.1537282756"}    
    MetersToLatLon = (minx, maxx, miny, maxy)
    osg.Layer.GetExtents() =  (18241443.028818697, 18745720.322112225, -2596125.9020476588, -2265080.9167815968)
    """
    if not entity.key().name():
        return
    if entity.key().name().rfind('jetz') != -1:        
        logging.info('Fixing extent for %s' % entity.key().name())
        info = simplejson.loads(entity.info)
        extents = MetersToLatLon((
            float(info['extentNorthWest'].split(',')[1]),  # minx
            float(info['extentSouthEast'].split(',')[1]),  # maxx
            float(info['extentSouthEast'].split(',')[0]),  # miny
            float(info['extentNorthWest'].split(',')[0]))) # maxy
        fixed_info = dict(
            extentNorthWest='%s,%s' % (extents[0], extents[3]),
            extentSouthEast='%s,%s' % (extents[1], extents[2]),
            proj=info['proj'])
        entity.info = db.Text(simplejson.dumps(fixed_info))
        logging.info('ENTITY=' + str(entity.info))
        yield op.db.Put(entity)        
    
def build_metadata_index(entity):
    """Builds and puts() a MetaDataIndex entity for each MetaData entity."""
    md = simplejson.loads(entity.object)
    md_name = md.get('name')
    if md_name:
        md_name = md_name.lower()
    md_source = md.get('source')
    if md_source:
        md_source = md_source.lower()
    md_description = md.get('description')
    if md_description:
        md_description = md_description.lower()

    # Builds keywords list:
    keywords = []
    for x in [md_name, md_source, md_description]:
        if not x:
            continue
        keywords.append(x.strip().lower())
        keywords.extend(explode(x))

    yield op.db.Put(
        MetaDataIndex(
            parent=entity,
            data_name=md_name,
            data_source=md_source,
            keywords=keywords))

def change_occurrenceset_key(entity):
    """Changes an OccurrenceSet entity key.

    Note: Entity keys are immutable, so we're just creating a new OccurrenceSet 
    entity and deleting the old one.

    Incoming OccurrenceSet key_names look like this:
        wwf/ecoregion/id
        wdpa/pa/id

    We want to change key_names so that they look like this:
        wwf/ecoregion-group/id
        wdpa/pa-group/id
    
    The following entities have an OccurrenceSet parent, so their keys need
    to change as well. Again, since keys are immutable, these entities will
    be deleted and new ones will be created:
        OccurrenceSetIndex
        MasterSearchIndex

    The following entities have an OccurrenceSet ReferenceProperty which will
    get replaced:
        OccurrenceIndex
    
    Arguments:
        entity - An OccurrenceSet entity

    """
    # Calculates the new OccurrenceSet key_name:
    key_name = entity.key().name()
    if key_name.rfind('ecoregion') > -1:
        new_key_name = key_name.replace('ecoregion', 'ecoregion-group')
    elif key_name.rfind('pa') > -1:
        new_key_name = key_name.replace('pa', 'pa-group')

    # Creates the new OccurrenceSet entity:
    yield op.db.Put(OccurrenceSet(
            key_name=new_key_name,
            name = entity.name,
            subname = entity.subname,
            source = entity.source,
            category = entity.category,
            info = entity.info,
            dateCreated = entity.dateCreated))
    
    new_key = db.Key.from_path('OccurrenceSet', new_key_name)

    # Updates all OccurrenceSet decendants with a new parent:
    for decendent in db.query_descendants(entity):
        kind = decendent.key().kind()
        if  kind == 'OccurrenceSetIndex':
            new_decendant = OccurrenceSetIndex(
                parent=new_key,
                term=decendent.term,
                rank=decendent.rank)
        elif kind == 'MasterSearchIndex':
            new_decendant = MasterSearchIndex(
                parent=new_key,
                term=decendent.term,
                rank=decendent.rank)
        else:
            logging.error('Unknown decendant of OccurrenceSet: %s' % decendant)
            continue
        yield op.db.Put(new_decendant)
        yield op.db.Delete(decendent)

    # Updates reference property in OccurrenceSetIndex:
    osi = entity.polygons.get()
    if osi:
        osi.occurrenceSet = new_key
        yield op.db.Put(osi)

    # Deletes the OccurrenceSet:
    yield op.db.Delete(entity)
    
def delete(entity):
    """Deletes the entity from the datastore."""
    #if len(entity.key().name().split('/')[1]) < 6:
    
    yield op.db.Delete(entity)

def clean_term_index(entity):
    """Cleans term indexes of terms pointing to old layers"""
    #if len(entity.key().name().split('/')[1]) < 6:
    p = entity.key().parent()
    if db.get(p) is None:
        logging.info(str(entity.key()) + " deleted")
        yield op.db.Delete(entity)
    else:
        pass
        
def move_index_to_mastersearch(entity):
    #multipoly, done
    ms = MasterSearchIndex(
        key_name = entity.key().name(),
        parent = entity.key().parent(),
        term = entity.term,
        rank = entity.rank )
    yield op.db.Put(ms)
    
def clean_empty_os(entity):
    #os
    res = 0
    try:
        res = len(entity.polygons.fetch(1))
    except:
        res = 0
    if entity.name == 'Bufo bufo':
        logging.error('Bufo bufo: %s' % res)
    if res==0:
        yield op.db.Delete(entity)

def change_mol_to_iucn(entity):
    if entity.source == 'MOL' and entity.subname=='MOL Range Map':
        entity.source = 'IUCN'
        entity.subname = 'IUCN Range Map'
        yield op.db.Put(entity)

