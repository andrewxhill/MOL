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

import cStringIO
import datetime
import logging
import simplejson
import StringIO
import urllib
from xml.etree import ElementTree as etree

def name_url(name):
    params = urllib.urlencode(dict(query=name,view='json'))
    return 'http://data.gbif.org/species/nameSearch?%s' % params

def name_list(content):
    return simplejson.loads(content)['Resultset']['Result']

def get_points(name, content=None, limit=100):
    points = []
    url = None
    if content:
        records = _get_records(content)
        points = [(r['decimalLatitude'], r['decimalLongitude']) for r in records]
        next_url = _get_next_url(content)
        if next_url:           
            url = next_url
    else:
        url = _get_url(name, limit=limit)
    logging.info('gbif name %s - %s (%s)' % (name, url, len(points)))
    return points, url

def _get_next_url(content):
    try:
        return content.split('nextRequestUrl>')[1].split('<')[0].replace("&amp;", '&')
    except:
        return None

def _get_url(name, limit=100, offset=0):
    params = urllib.urlencode(dict(
            format='darwin',
            coordinateStatus=True,
            maxResults=limit,
            startIndex=0,
            scientificname=name))
    return 'http://data.gbif.org/ws/rest/occurrence/list?%s' % params

def _get_records(content):
    json = _xmltojson(content)
    records = []
    for provider in json['records']['publishers']:
        for resource in provider['resources']:
            for occurrence in resource['occurrences']:
                records.append(occurrence['coordinates'])
    return records

def _xmltojson(xmldata):
    NSXML = "http://portal.gbif.org/ws/response/gbif"
    TOXML = "http://rs.tdwg.org/ontology/voc/TaxonOccurrence#"
    xml = etree.iterparse(cStringIO.StringIO(xmldata), ("start", "end"))
    out = {"publishers":[]}
    provider, resource, occurrence = {"resources": []}, {"occurrences": []}, {"coordinates": {"coordinateUncertaintyInMeters": None,"decimalLongitude": None,"decimalLatitude": None}}
    p, r, o = True, False, False
    pct, rct, oct = 0, 0, 0
    for action, element in xml:
        if "{%s}TaxonOccurrence" % TOXML == element.tag:
            if action=="start":
                p, r, o = False, False, True
                #logging.error(o)
            elif action=="end":
                oct+=1
                resource['occurrences'].append(occurrence)
                occurrence = {"coordinates": {"coordinateUncertaintyInMeters": None,"decimalLongitude": None,"decimalLatitude": None}}

        elif "{%s}dataResource" % NSXML == element.tag:
            if action=="start":
                p, r, o = False, True, False
            elif action=="end":
                rct+=1
                provider['resources'].append(resource)
                resource = {'occurrences':[]}

        elif "{%s}dataProvider" % NSXML == element.tag:
            if action=="start":
                p, r, o = True, False, False
            elif action=="end":
                pct+=1
                out["publishers"].append(provider)
                provider = {"resources": []}

        elif p or r:
            if "{%s}name" % NSXML == element.tag:
                if p:
                    provider['name'] = element.text
                elif r:
                    resource['name'] = element.text
        elif o:
            if element.tag in ["{%s}decimalLatitude" % TOXML, "{%s}decimalLongitude" % TOXML]:
                try:
                    occurrence["coordinates"][str(element.tag).split("}")[1]] = float(element.text)
                except:
                    occurrence["coordinates"][str(element.tag).split("}")[1]] = None
            elif "{%s}coordinateUncertaintyInMeters" % TOXML == element.tag:
                try:
                    occurrence["coordinates"]["coordinateUncertaintyInMeters"] = float(element.text)
                    assert occurrence["coordinates"]["coordinateUncertaintyInMeters"] > 0
                except:
                    occurrence["coordinates"]["coordinateUncertaintyInMeters"] = None
    logging.error(oct)
    return {"source": "GBIF", "accessDate": str(datetime.datetime.now()), "totalPublishers": pct, "totalResources": rct, "totalRecords": oct, "records": out}
