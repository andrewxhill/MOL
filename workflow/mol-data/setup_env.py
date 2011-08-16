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

import os
import sys

if not hasattr(sys, 'version_info'):
  sys.stderr.write('Very old versions of Python are not supported. Please '
                   'use version 2.5 or greater.\n')
  sys.exit(1)
version_tuple = tuple(sys.version_info[:2])
if version_tuple < (2, 4):
  sys.stderr.write('Error: Python %d.%d is not supported. Please use '
                   'version 2.5 or greater.\n' % version_tuple)
  sys.exit(1)

DIR_PATH = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
DIR_PATH = reduce(lambda x,y: '%s%s%s' % (x,os.path.sep,y), DIR_PATH.split(os.path.sep)[:-2])
SCRIPT_DIR = os.path.join(DIR_PATH, 'workflow')

EXTRA_PATHS = [
  DIR_PATH,
  SCRIPT_DIR,
  os.path.join(DIR_PATH, 'lib', 'google_appengine'),
  os.path.join(DIR_PATH, 'lib', 'google_appengine', 'lib', 'antlr3'),
  os.path.join(DIR_PATH, 'lib', 'google_appengine', 'lib', 'django_0_96'),
  os.path.join(DIR_PATH, 'lib', 'google_appengine', 'lib', 'fancy_urllib'),
  os.path.join(DIR_PATH, 'lib', 'google_appengine', 'lib', 'ipaddr'),
  os.path.join(DIR_PATH, 'lib', 'google_appengine', 'lib', 'protorpc'),
  os.path.join(DIR_PATH, 'lib', 'google_appengine', 'lib', 'webob'),
  os.path.join(DIR_PATH, 'lib', 'google_appengine', 'lib', 'yaml', 'lib'),
  os.path.join(DIR_PATH, 'lib', 'google_appengine', 'lib', 'simplejson'),
  os.path.join(DIR_PATH, 'lib', 'google_appengine', 'lib', 'graphy'),
  os.path.join(DIR_PATH, 'lib', 'dsplus'),
  os.path.join(DIR_PATH, 'app'),
]

SCRIPT_EXCEPTIONS = {
}

def fix_sys_path():
  """Fix the sys.path to include our extra paths."""
  sys.path = EXTRA_PATHS + sys.path
  #print sys.path
