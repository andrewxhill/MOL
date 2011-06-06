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

- OccurrenceSetIndex (parent)
- MasterSearchIndex (parent)
- OccurenceIndex (reference)


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
    key_name = entity.key.name()
    if key_name.rfind('ecoregion') > -1:
        new_key_name = key_name.replace('ecoregion', 'ecoregion-group')
    elif key_name.rfind('pa') > -1:
        new_key_name = key_name.replace('pa', 'pa-group')

    # Creates the new OccurrenceSet entity:
    new_key = OccurrenceSet(
        key_name=new_key_name,
        name = entity.name,
        subname = entity.subname,
        source = entity.source,
        category = entity.category,
        info = entity.info,
        dateCreated = entity.dateCreated).put()
    
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
        new_decendant.put()
        decendent.delete()

    # Updates reference property in OccurrenceSetIndex:
    for osi in entity.polygons.get():
        osi.occurrenceSet = new_key
        osi.put()

    # Deletes the OccurrenceSet:
    entity.delete()
    
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


