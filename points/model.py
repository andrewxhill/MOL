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

__author__ = "Aaron Steele (eightysteele@gmail.com)"

import logging
import os
import simplejson

from sdl import interval

from ndb.model import Model, Key, FloatProperty, IntegerProperty, StringProperty
from ndb import query, model

class Point(model.Model):
    lat = model.FloatProperty('x', indexed=False)
    lng = model.FloatProperty('y', indexed=False)
    record = model.StringProperty('r', indexed=False)

class PointIndex(model.Model):
    lat = model.FloatProperty('y', indexed=False)
    lng = model.FloatProperty('x', indexed=False)
    source = model.StringProperty('s')
    name = model.StringProperty('n')
    x0 = model.IntegerProperty()
    x1 = model.IntegerProperty()
    x2 = model.IntegerProperty()
    x3 = model.IntegerProperty()
    x4 = model.IntegerProperty()
    x5 = model.IntegerProperty()
    x6 = model.IntegerProperty()
    x7 = model.IntegerProperty()
    x8 = model.IntegerProperty()
    x9 = model.IntegerProperty()
    x10 = model.IntegerProperty()
    x11 = model.IntegerProperty()
    x12 = model.IntegerProperty()
    x13 = model.IntegerProperty()
    x14 = model.IntegerProperty()
    x15 = model.IntegerProperty()
    x16 = model.IntegerProperty()
    x17 = model.IntegerProperty()
    x18 = model.IntegerProperty()
    x19 = model.IntegerProperty()
    x20 = model.IntegerProperty()
    x21 = model.IntegerProperty()
    x22 = model.IntegerProperty()
    x23 = model.IntegerProperty()
    x24 = model.IntegerProperty()
    x25 = model.IntegerProperty()
    x26 = model.IntegerProperty()
    y0 = model.IntegerProperty()
    y1 = model.IntegerProperty()
    y2 = model.IntegerProperty()
    y3 = model.IntegerProperty()
    y4 = model.IntegerProperty()
    y5 = model.IntegerProperty()
    y6 = model.IntegerProperty()
    y7 = model.IntegerProperty()
    y8 = model.IntegerProperty()
    y9 = model.IntegerProperty()
    y10 = model.IntegerProperty()
    y11 = model.IntegerProperty()
    y12 = model.IntegerProperty()
    y13 = model.IntegerProperty()
    y14 = model.IntegerProperty()
    y15 = model.IntegerProperty()
    y16 = model.IntegerProperty()
    y17 = model.IntegerProperty()
    y18 = model.IntegerProperty()
    y19 = model.IntegerProperty()
    y20 = model.IntegerProperty()
    y21 = model.IntegerProperty()
    y22 = model.IntegerProperty()
    y23 = model.IntegerProperty()
    y24 = model.IntegerProperty()
    y25 = model.IntegerProperty()

    @classmethod
    def create(cls, lat, lng, name, source):
        pi = PointIndex(
            lng=float(lng), 
            lat=float(lat),
            name=name.strip().lower(), 
            source=source.strip().lower())
        
        # Longitude (x)
        var_min = -180 * pow(10, 5)
        var_max =  180 * pow(10, 5)    
        varval = int(lng * pow(10, 5)) 
        intervals = interval.get_index_intervals(varval, var_min, var_max)
        for index,value in intervals.iteritems():
            model.IntegerProperty(name=index.replace('i', 'x'))._store_value(pi, value)

        # Latitude (y)
        var_min = -90 * pow(10, 5)
        var_max =  90 * pow(10, 5)
        varval = int(lat * pow(10, 5)) 
        intervals = interval.get_index_intervals(varval, var_min, var_max)
        for index,value in intervals.iteritems():
            model.IntegerProperty(name=index.replace('i', 'y'))._store_value(pi, value)

        pi._fix_up_properties()

        return pi
