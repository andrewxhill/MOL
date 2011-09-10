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
__contributors__ = []

import logging
import os
import simplejson

from ndb.model import Model, Key, StringProperty, TextProperty, DateTimeProperty

class CacheItem(Model):
    value = TextProperty('v', required=True)
    created = DateTimeProperty('c', auto_now_add=True)
    
    @classmethod
    def get(cls, key, loads=False):
        item = Key(cls.__name__, key.strip().lower()).get()
        value = None
        if item:            
            if loads:
                value = simplejson.loads(item.value)
            else:
                value = item.value
        return value

    @classmethod
    def add(cls, key, value):
        cls(id=key.strip().lower(), value=simplejson.dumps(value)).put()
    
def get(key):
    return CacheItem.get(key)

def add(key, value):
    CacheItem.add(key, value)
        
