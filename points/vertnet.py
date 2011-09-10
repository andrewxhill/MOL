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

try:
    appid = os.environ['APPLICATION_ID']
    appver = os.environ['CURRENT_VERSION_ID'].split('.')[0]
except:
    pass

if 'SERVER_SOFTWARE' in os.environ:
    PROD = not os.environ['SERVER_SOFTWARE'].startswith('Development')
    HOST = 'localhost:8888'
else:
    PROD = True
    HOST = '%s.vert-net.appspot.com' % appver

def name_url(name):
    params = urllib.urlencode(dict(q=name, limit=100))
    return 'http://%s/api/search?%s' % (HOST, params)

def name_list(content):
    names = set([r.get('scientificname', '') for r in \
                     simplejson.loads(content)['records']])
    if '' in names:
        names.remove('')
    return list(names)

    
