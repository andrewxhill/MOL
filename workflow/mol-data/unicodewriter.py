#!/usr/bin/env python
#
# Copyright 2011 Aaron Steele and John Wieczorek
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

''' 
Code copied directly from http://docs.python.org/library/csv.html#csv-examples and modified
to support fieldnames. Also, `UnicodeReader.next()` is returns dictionaries and 
`UnicodeWriter.writerow` takes a dictionary - all to support DictWrite and DictReader-like
behavior.
 
Necessary to overcome deficiency in Python 2.7 csv.DictWriter class when trying 
to output Unicode.
'''

import csv, codecs, cStringIO, sys

class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")

class UnicodeDictReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)
        self.header = self.reader.next()

    def next(self):
        row = self.reader.next()
        vals = [unicode(s, "utf-8") for s in row]
        return dict((self.header[x], vals[x]) for x in range(len(self.header)))

    def __iter__(self):
        return self

class UnicodeDictWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, fieldnames, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.fieldnames = fieldnames
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()
        
    def writeheader(self):
        self.writer.writerow(self.fieldnames)

    def writerow(self, row):
        values = []
        
        # Some (most?) rows don't have all the keys possible
        # in the file. In such cases, we need to make sure we
        # insert a blank string in their place.
        for fieldname in self.fieldnames:
            if row.has_key(fieldname) and row[fieldname] is not None:
                if isinstance(row[fieldname], unicode):
                    values.append(row[fieldname])
                else:
                    values.append(unicode(row[fieldname]))
            else:
                values.append("")

        self.writer.writerow([str.encode('utf-8') for str in values])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


if __name__ == '__main__':
    args = sys.argv
    if len(args) > 1:
        # Make sure your file header is: id,name,age
        filename = sys.argv[1]
    else:
        filename = 'data.csv'
        data = u"id,name,age\n0,aaron,34\n1,john\u00A9,50\n"
        f = codecs.open(filename, encoding='utf-8', mode='w')
        f.write(data)
        f.close()
    r = UnicodeDictReader(open(filename, 'r'), skipinitialspace=True)
    w = UnicodeDictWriter(open(filename.replace('.csv', '.out.csv'), 'w'), ['id', 'name', 'age'])
    w.writeheader()
    for row in r:
        print row
        w.writerow(row)
    print "All done."
        
