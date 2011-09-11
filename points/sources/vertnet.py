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

import os
import simplejson
import urllib

#HOST = 'localhost:8888'
HOST = 'canary.vert-net.appspot.com'

def name_url(name):
    params = urllib.urlencode(dict(q=name, limit=100))
    return 'http://%s/api/search?%s' % (HOST, params)

def name_list(content):
    names = set([r.get('scientificname', '') for r in \
                     simplejson.loads(content)['records']])
    if '' in names:
        names.remove('')
    return list(names)

def get_points(name, content=None, limit=100):
    points = []
    url = None
    if content:
        records = simplejson.loads(content)['records']
        points = [(r['decimallatitude'], r['decimallongitude']) for r in records]
        offset = simplejson.loads(content)['next_offset']
        if offset:           
            params = urllib.urlencode(dict(q=name, limit=limit, offset=offset))
            url = 'http://%s/api/search?%s' % (HOST, params)
    else:
        params = urllib.urlencode(dict(q=name, limit=limit))
        url = 'http://%s/api/search?%s' % (HOST, params)
    return points, url
