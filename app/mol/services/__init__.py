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

from mol.db import TmpTiles

from google.appengine.ext import db

from math import ceil
import png
import cStringIO
from google.appengine.api.datastore_file_stub import DatastoreFileStub

bEncode = {'0':'A',
           '1':'B',
           '2':'C',
           '3':'D',
           '4':'E',
           '5':'F',
           '6':'G',
           '7':'H',
           '8':'I',
           '9':'J',
           '10':'K',
           '11':'L',
           '12':'M',
           '13':'N',
           '14':'O',
           '15':'P',
           '16':'Q',
           '17':'R',
           '18':'S',
           '19':'T',
           '20':'U',
           '21':'V',
           '22':'W',
           '23':'X',
           '24':'Y',
           '25':'Z',
           '26':'a',
           '27':'b',
           '28':'c',
           '29':'d',
           '30':'e',
           '31':'f',
           '32':'g',
           '33':'h',
           '34':'i',
           '35':'j',
           '36':'k',
           '37':'l',
           '38':'m',
           '39':'n',
           '40':'o',
           '41':'p',
           '42':'q',
           '43':'r',
           '44':'s',
           '45':'t',
           '46':'u',
           '47':'v',
           '48':'w',
           '49':'x',
           '50':'y',
           '51':'z',
           '52':'0',
           '53':'1',
           '54':'2',
           '55':'3',
           '56':'4',
           '57':'5',
           '58':'6',
           '59':'7',
           '60':'8',
           '61':'9',
           '62':'+',
           '63':'/'}

bDecode = {'+':'111110',
           '/':'111111',
           '0':'110100',
           '1':'110101',
           '2':'110110',
           '3':'110111',
           '4':'111000',
           '5':'111001',
           '6':'111010',
           '7':'111011',
           '8':'111100',
           '9':'111101',
           'A':'000000',
           'B':'000001',
           'C':'000010',
           'D':'000011',
           'E':'000100',
           'F':'000101',
           'G':'000110',
           'H':'000111',
           'I':'001000',
           'J':'001001',
           'K':'001010',
           'L':'001011',
           'M':'001100',
           'N':'001101',
           'O':'001110',
           'P':'001111',
           'Q':'010000',
           'R':'010001',
           'S':'010010',
           'T':'010011',
           'U':'010100',
           'V':'010101',
           'W':'010110',
           'X':'010111',
           'Y':'011000',
           'Z':'011001',
           'a':'011010',
           'b':'011011',
           'c':'011100',
           'd':'011101',
           'e':'011110',
           'f':'011111',
           'g':'100000',
           'h':'100001',
           'i':'100010',
           'j':'100011',
           'l':'100101',
           'm':'100110',
           'n':'100111',
           'p':'101001',
           'q':'101010',
           's':'101100',
           't':'101101',
           'u':'101110',
           'v':'101111',
           'w':'110000',
           'x':'110001',
           'y':'110010',
           'z':'110011'}

class TileService(object):
  @staticmethod
  def get_png_tile(url):
  #convert the URL route into the key (removing .png)
    print url
    assert '/' == url[0]
    path = url[1:]
    if '/' in path:
      (b1, b2, k) = path.split("/", 2)
      k = k.split('.')[0]
    else:
      k = '00/210'
    key = "%s/%s" % (k, 'presence')
    print 'getting key %s' % key
    key = db.Key.from_path('TmpTiles', key)
    t = TmpTiles.get(key)
    if t:
      chk = lambda v, l: [v[i * l:(i + 1) * l] for i in
                          range(int(ceil(len(v) / float(l))))]
      #fix = lambda v: int(c) for c in v
      b = ''
      for c in t.band:
        b += bDecode[c]

      #we should try to combine the follow two steps into a single function
      s = chk(b[:-3], 256)
      s = map(lambda x: map(int, x), s)

      f = cStringIO.StringIO()
      palette = [(0xff, 0xff, 0xff, 0x00), (0x00, 0x00, 0x00, 0xff)]
      w = png.Writer(256, 256, palette=palette, bitdepth=1)
      w.write(f, s)
      return f

from google.appengine.api import apiproxy_stub
from google.appengine.api import apiproxy_stub_map

class DatastoreTestStub(apiproxy_stub.APIProxyStub):
  def __init__(self):
    super(DatastoreTestStub, self).__init__('datastore_v3')

  def _Dynamic_Put(self, put_request, put_response):
    print put_request

  def _Dynamic_Get(self, get_request, get_response):
    print get_request
    

if __name__ == '__main__':
  import os
  from google.appengine.datastore import datastore_pb
  os.environ['SERVER_SOFTWARE'] = 'Development via nose'
  os.environ['SERVER_NAME'] = 'Foo'
  os.environ['SERVER_PORT'] = '8080'
  os.environ['APPLICATION_ID'] = 'test-app-run'
  os.environ['USER_EMAIL'] = 'test@example.com'
  os.environ['CURRENT_VERSION_ID'] = 'testing-version'

  apiproxy_stub_map.apiproxy.RegisterStub('datastore_v3', DatastoreFileStub('test-app-run', None, None))

  key = u'01/21/presence'
  tile = TmpTiles(key=db.Key.from_path('TmpTiles', key))
  tile.put()
  url = '/api/zoom/tiles?k=01/21'
  print TileService.get_png_tile(url)
  
