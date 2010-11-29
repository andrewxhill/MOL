from google.appengine.ext import bulkload
from google.appengine.api import datastore_types
from google.appengine.ext import db

import DataStore

class LoadRanges(bulkload.Loader):
    def __init__(self):
        bulkload.Loader.__init__(self, 'SpeciesRanges', [('rowid',int),
                                                         ('specid',int),
                                                         ('tilex',int),
                                                         ('tiley',int),
                                                         ('status',int),
                                                         ('floatval',float),
                                                         ('intval',int),
                                                         ])

if __name__ == '__main__':
    bulkload.main(LoadRanges())

"""


    - property: rowid
      external_name: rowid
      import_transform: transform.none_if_empty(int)
      
    - property: specid
      external_name: specid
      import_transform: transform.none_if_empty(int)
      
    - property: tilex
      external_name: tilex
      import_transform: transform.none_if_empty(int)
      
    - property: tiley
      external_name: tiley
      import_transform: transform.none_if_empty(int)
      
    - property: zoom
      external_name: zoom
      import_transform: transform.none_if_empty(int)
      
    - property: status
      external_name: status
      import_transform: transform.none_if_empty(int)
      
    - property: floatval
      external_name: floatval
      import_transform: transform.none_if_empty(float)
      
    - property: intval
      external_name: intval
      import_transform: transform.none_if_empty(int)
  
"""
