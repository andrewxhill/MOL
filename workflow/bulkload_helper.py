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

"""This module contains transformation functions for the bulkloader."""

# Fix sys.path
from setup_env import fix_sys_path
fix_sys_path()

# MoL imports
from mol.db import Layer, LayerIndex, LayerPolygon

# Python imports
import copy
import logging
import sys

# Goole App Engine imports
from django.utils import simplejson
from google.appengine.ext.bulkload import transform
from google.appengine.ext import db
from google.appengine.api import datastore

# Datastore Plus imports
from ndb import query, model

STOP_WORDS = [
    'a', 'able', 'about', 'across', 'after', 'all', 'almost', 'also', 'am', 
    'among', 'an', 'and', 'any', 'are', 'as', 'at', 'be', 'because', 'been', 
    'but', 'by', 'can', 'cannot', 'could', 'dear', 'did', 'do', 'does', 'either', 
    'else', 'ever', 'every', 'for', 'from', 'get', 'got', 'had', 'has', 'have', 
    'he', 'her', 'hers', 'him', 'his', 'how', 'however', 'i', 'if', 'in', 'into', 
    'is', 'it', 'its', 'just', 'least', 'let', 'like', 'likely', 'may', 'me', 
    'might', 'most', 'must', 'my', 'neither', 'no', 'nor', 'not', 'of', 'off', 
    'often', 'on', 'only', 'or', 'other', 'our', 'own', 'rather', 'said', 'say', 
    'says', 'she', 'should', 'since', 'so', 'some', 'than', 'that', 'the', 'their', 
    'them', 'then', 'there', 'these', 'they', 'this', 'tis', 'to', 'too', 'twas', 
    'us', 'wants', 'was', 'we', 'were', 'what', 'when', 'where', 'which', 'while', 
    'who', 'whom', 'why', 'will', 'with', 'would', 'yet', 'you', 'your']

DO_NOT_FULL_TEXT = []

def create_layer_json():
    def wrapper(value, bulkload_state):
        """Returns a Record key built from value.
        
        Arguments:
            value - urlsafe key string created by model.Key.urlsafe()            
        """
        d = copy.deepcopy(bulkload_state.current_dictionary)
        d.pop('__record_number__')
        return db.Text(simplejson.dumps(d))
    return wrapper

def create_layer_index_key():
    def wrapper(value, bulkload_state): 
        d = bulkload_state.current_dictionary
        d['lname'] = '%s-%s-%s' % (d['layer_source'], d['layer_collection'], d['layer_filename'])
        return transform.create_deep_key(
            ('Layer', 'lname'),
            ('LayerIndex', 'lname'))(value, bulkload_state)
    return wrapper

def get_corpus_list():
    def wrapper(value, bulkload_state):
        # TODO make this recursive for nested dictionary.
        d = bulkload_state.current_dictionary
        corpus = set(
            [x.strip().lower() for key,x in d.iteritems() \
                 if isinstance(x, unicode) and key.strip().lower() not in DO_NOT_FULL_TEXT and \
                 x.strip().lower() not in STOP_WORDS]) 
        corpus.update(
            reduce(lambda x,y: x+y, 
                   map(lambda x: [s.strip().lower() for s in x.split() if s], 
                       [val for key,val in d.iteritems() \
                            if isinstance(val, unicode) and key.strip().lower() not in DO_NOT_FULL_TEXT and \
                            val.strip().lower() not in STOP_WORDS]))) # adds tokenized values      
        return list(corpus)
    return wrapper

def get_polygons():
    def wrapper(value, bulkload_state):
        try:
            polygons = []
            dbf = simplejson.loads(value)
            logging.info('dbf=%s' % dbf)
            for p in dbf:
                polygons.append(datastore.Entity(
                        'LayerPolygon',
                        polygonid=p['polygonid'],
                        areaid=p['areaid'],
                        specieslatin=p['specieslatin'],
                        source=p['source']))
            return polygons
        except Exception as e:
            logging.error(e)
            sys.exit(1)
    return wrapper

def get_poly(input_dict, instance, bulkload_state_copy):    
    logging.info('instance=%s' % instance)
    return instance

def add_dynamic_properties(input_dict, instance, bulkload_state_copy):    
    """Adds dynamic properties from the CSV input_dict to the entity instance."""
    recjson = simplejson.loads(input_dict['recjson'])    
    for key,value in recjson.iteritems():
        if key in DO_NOT_INDEX or value.strip() == '':
            continue
        key_name = None

        # Set Darwin Core dynamic property name to the alias
        if key in common.DWC_TO_ALIAS.keys():
            key_name = common.DWC_TO_ALIAS[key]
        else:
            if key in common.ALIAS_TO_DWC.keys():
                key_name = key
        if key_name is None:
            #logging.info('Skipping unknown column %s=%s' % (key, value))
            continue
        try:
            instance[key_name] = value.lower()
        except:
            pass

    # Do not bulkload CSV records that have recstate equal to 'deleted'
    recstate = input_dict['recstate'] #instance.pop('recstate')
    if recstate == 'deleted':
        return datastore.Entity('RecordIndex')

    return instance

