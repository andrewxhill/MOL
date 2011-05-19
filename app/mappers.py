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


