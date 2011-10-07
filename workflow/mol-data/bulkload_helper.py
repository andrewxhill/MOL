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
from mol.db.layers import Layer, LayerIndex, LayerPolygon

# Python imports
import copy
import csv
import logging
import os
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

DO_NOT_INDEX= []

def create_layer_json():
    def wrapper(value, bulkload_state):
        """Returns current_dictionary (a row in the CSV file) as JSON text."""
        path, filename = os.path.split(bulkload_state.filename)
        jsonfilename = os.path.join(path, 'collection.polygons.csv.txt')
        dr = csv.DictReader(open(jsonfilename, 'r'))
        layer_filename = bulkload_state.current_dictionary['layer_filename']
        for row in dr:
            if row['shapefilename'] == layer_filename:                
                d = copy.deepcopy(bulkload_state.current_dictionary)
                d = dict((k,v) for k,v in d.iteritems() if v and v != 'null')
                d.pop('__record_number__') # We don't want this in the JSON!
                
                # TODO: polygonid and bibliographicitation are magically appearing in d
                # so pop them here.
                #d.pop('polygonid') # We don't want this in the JSON!
                if d.has_key('bibliographiccitation'):
                    d.pop('bibliographiccitation') # We don't want this in the JSON!

                polygons = simplejson.loads(row['json'])
                d['polygons'] = polygons
                return db.Text(simplejson.dumps(d, ensure_ascii=False))
        return None
    return wrapper

def create_layer_index_key():
    """Returns a function that returns a LayerIndex key with Layer parent."""
    def wrapper(value, bulkload_state): 
        d = bulkload_state.current_dictionary
        d['layer_key_name'] = value 
        return transform.create_deep_key(
            ('Layer', 'layer_key_name'),
            ('LayerIndex', 'polygonid'))(value, bulkload_state)
    return wrapper

def get_corpus_list():
    """Returns a function that returns a list of full text words."""
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

def add_polygon(input_dict, instance, bulkload_state_copy):
    json = {}
    # Required
    val = transform.none_if_empty(unicode)(input_dict['areaid'])
    instance['polygon.areaid'] = transform.none_if_empty(unicode)(input_dict['areaid'])
    if val:
        json['areaid'] = transform.none_if_empty(unicode)(input_dict['areaid'])
    val = transform.none_if_empty(unicode)(input_dict['bibliographiccitation'])
    instance['polygon.bibliographiccitation'] = transform.none_if_empty(unicode)(input_dict['bibliographiccitation'])
    if val:
        json['bibliographiccitation'] = transform.none_if_empty(unicode)(input_dict['bibliographiccitation'])
    val = transform.none_if_empty(unicode)(input_dict['contact'])
    instance['polygon.contact'] = transform.none_if_empty(unicode)(input_dict['contact'])
    if val:
        json['contact'] = transform.none_if_empty(unicode)(input_dict['contact'])
    val = transform.none_if_empty(unicode)(input_dict['creator'])
    instance['polygon.creator'] = transform.none_if_empty(unicode)(input_dict['creator'])
    if val:
        json['creator'] = transform.none_if_empty(unicode)(input_dict['creator'])
    val = transform.none_if_empty(unicode)(input_dict['identifier'])
    instance['polygon.identifier'] = transform.none_if_empty(unicode)(input_dict['identifier'])
    if val:
        json['identifier'] = transform.none_if_empty(unicode)(input_dict['identifier'])
    val = transform.none_if_empty(unicode)(input_dict['type'])
    instance['polygon.type'] = transform.none_if_empty(unicode)(input_dict['type'])
    if val:
        json['type'] = transform.none_if_empty(unicode)(input_dict['type'])
    val = transform.none_if_empty(unicode)(input_dict['datesubmitted'])
    instance['polygon.datesubmitted'] = transform.none_if_empty(unicode)(input_dict['datesubmitted'])
    if val:
        json['datesubmitted'] = transform.none_if_empty(unicode)(input_dict['datesubmitted'])
    val = transform.none_if_empty(unicode)(input_dict['rights'])
    instance['polygon.rights'] = transform.none_if_empty(unicode)(input_dict['rights'])
    if val:
        json['rights'] = transform.none_if_empty(unicode)(input_dict['rights'])
    val = transform.none_if_empty(unicode)(input_dict['scientificname'])
    instance['polygon.scientificname'] = transform.none_if_empty(unicode)(input_dict['scientificname'])
    if val:
        json['scientificname'] = transform.none_if_empty(unicode)(input_dict['scientificname'])
    val = transform.none_if_empty(unicode)(input_dict['verbatimsrs'])
    instance['polygon.verbatimsrs'] = transform.none_if_empty(unicode)(input_dict['verbatimsrs'])
    if val:
        json['verbatimsrs'] = transform.none_if_empty(unicode)(input_dict['verbatimsrs'])
    # Optional
    val = transform.none_if_empty(str)(input_dict['abundance'])
    instance['polygon.abundance'] = transform.none_if_empty(unicode)(input_dict['abundance'])
    if val:
        json['abundance'] = transform.none_if_empty(unicode)(input_dict['abundance'])
    val = transform.none_if_empty(str)(input_dict['abundanceunits'])
    instance['polygon.abundanceunits'] = transform.none_if_empty(unicode)(input_dict['abundanceunits'])
    if val:
        json['abundanceunits'] = transform.none_if_empty(unicode)(input_dict['abundanceunits'])
    val = transform.none_if_empty(str)(input_dict['areaname'])
    instance['polygon.areaname'] = transform.none_if_empty(unicode)(input_dict['areaname'])
    if val:
        json['areaname'] = transform.none_if_empty(unicode)(input_dict['areaname'])
    val = transform.none_if_empty(str)(input_dict['vernacularname'])
    instance['polygon.vernacularname'] = transform.none_if_empty(unicode)(input_dict['vernacularname'])
    if val:
        json['vernacularname'] = transform.none_if_empty(unicode)(input_dict['vernacularname'])
    val = transform.none_if_empty(str)(input_dict['coverage'])
    instance['polygon.coverage'] = transform.none_if_empty(unicode)(input_dict['coverage'])
    if val:
        json['coverage'] = transform.none_if_empty(unicode)(input_dict['coverage'])
    val = transform.none_if_empty(str)(input_dict['establishmentmeans'])
    instance['polygon.establishmentmeans'] = transform.none_if_empty(unicode)(input_dict['establishmentmeans'])
    if val:
        json['establishmentmeans'] = transform.none_if_empty(unicode)(input_dict['establishmentmeans'])
    val = transform.none_if_empty(str)(input_dict['nameaccordingto'])
    instance['polygon.nameaccordingto'] = transform.none_if_empty(unicode)(input_dict['nameaccordingto'])
    if val:
        json['nameaccordingto'] = transform.none_if_empty(unicode)(input_dict['nameaccordingto'])
    val = transform.none_if_empty(str)(input_dict['occurrencestatus'])
    instance['polygon.occurrencestatus'] = transform.none_if_empty(unicode)(input_dict['occurrencestatus'])
    if val:
        json['occurrencestatus'] = transform.none_if_empty(unicode)(input_dict['occurrencestatus'])
    val = transform.none_if_empty(str)(input_dict['publisher'])
    instance['polygon.publisher'] = transform.none_if_empty(unicode)(input_dict['publisher'])
    if val:
        json['publisher'] = transform.none_if_empty(unicode)(input_dict['publisher'])
    val = transform.none_if_empty(str)(input_dict['samplingprotocol'])
    instance['polygon.samplingprotocol'] = transform.none_if_empty(unicode)(input_dict['samplingprotocol'])
    if val:
        json['samplingprotocol'] = transform.none_if_empty(unicode)(input_dict['samplingprotocol'])
    val = transform.none_if_empty(str)(input_dict['seasonality'])
    instance['polygon.seasonality'] = transform.none_if_empty(unicode)(input_dict['seasonality'])
    if val:
        json['seasonality'] = transform.none_if_empty(unicode)(input_dict['seasonality'])
    val = transform.none_if_empty(str)(input_dict['subject'])
    instance['polygon.subject'] = transform.none_if_empty(unicode)(input_dict['subject'])
    if val:
        json['subject'] = transform.none_if_empty(unicode)(input_dict['subject'])
    val = transform.none_if_empty(str)(input_dict['surveyenddate'])
    instance['polygon.surveyenddate'] = transform.none_if_empty(unicode)(input_dict['surveyenddate'])
    if val:
        json['surveyenddate'] = transform.none_if_empty(unicode)(input_dict['surveyenddate'])
    val = transform.none_if_empty(str)(input_dict['surveyintervals'])
    instance['polygon.surveyintervals'] = transform.none_if_empty(unicode)(input_dict['surveyintervals'])
    if val:
        json['surveyintervals'] = transform.none_if_empty(unicode)(input_dict['surveyintervals'])
    val = transform.none_if_empty(str)(input_dict['surveystartdate'])
    instance['polygon.surveystartdate'] = transform.none_if_empty(unicode)(input_dict['surveystartdate'])
    if val:
        json['surveystartdate'] = transform.none_if_empty(unicode)(input_dict['surveystartdate'])
    val = transform.none_if_empty(str)(input_dict['taxonid'])
    instance['polygon.taxonid'] = transform.none_if_empty(unicode)(input_dict['taxonid'])
    if val:
        json['taxonid'] = transform.none_if_empty(unicode)(input_dict['taxonid'])
    instance['json'] = db.Text(simplejson.dumps(json, ensure_ascii=False))
    return instance
