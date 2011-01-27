# -*- coding: utf-8 -*-
import MySQLdb, re, codecs
import simplejson, sys
from ruffus import *
from glob import glob

conn = MySQLdb.connect (host = "localhost",
                       port = 3306,
                       user = "username",
                       passwd = "password",
                       db = "col2010ac")
                       
synLog = open("IUCNGenSpecSynonymList-out.csv","w+")
waltLog = open("WaltIUCNSpecList-out.csv","w+")

synLines = 0 #discounts header
for q in open("IUCNGenSpecSynonymList.csv","r").readlines():
    synLines+=1
params = [[0,int(synLines)/4],
          [int(synLines/4),int(synLines/2)],
          [int(synLines/2),int(3*synLines/4)],
          [int(3*synLines/4),synLines]]
          
@parallel(params)
def SynOut(start,stop):
    cursor = conn.cursor ()
    result_file = open("%s.syn" % stop,"w+")
    lines = {}
    seen = {}
    i = 0
    for syn in open("IUCNGenSpecSynonymList.csv","r").readlines():
        if start<i and i<=stop:
            data = syn.split(',')
            spec = data[2].replace('"','')
            lines[i] = {'name': spec,'col_id': None,'syn_id': None,'syn_name': None}
            if spec in seen.keys():
                lines[i]['col_id'] = seen[spec]
            else:
                seen['name'] = None
                cursor.execute ("SELECT record_id FROM taxa WHERE name = '%s' LIMIT 1" % spec)
                r = cursor.fetchone()
                if r:
                    lines[i]['col_id'] = r[0]
                    seen['name'] = r[0]
            syn1 = "%s %s" % (data[6].replace('"',''),data[7].replace('"','').strip())
            lines[i]['syn_name'] = syn1
            cursor.execute ("SELECT record_id FROM taxa WHERE name = '%s' LIMIT 1" % syn1)
            r = cursor.fetchone()
            if r:
                lines[i]['syn_id'] = r[0]
        i+=1
    for l,p in lines.items():
        result_file.write("%s, %s, %s, %s\n" % (p['name'],p['col_id'],p['syn_name'],p['syn_id']))
    
iucnLines = 0 #discounts header
for q in open("WaltIUCNSpecList.csv","r").readlines():
    iucnLines+=1
walt_params = [[0,int(iucnLines)/4],
          [int(iucnLines/4),int(iucnLines/2)],
          [int(iucnLines/2),int(3*iucnLines/4)],
          [int(3*iucnLines/4),iucnLines]]


@parallel(walt_params)
def WaltOut(start,stop):
    cursor = conn.cursor ()
    result_file = open("%s.walt" % stop,"w+")
    lines = {}
    seen = {}
    i = 0
    for syn in open("WaltIUCNSpecList.csv","r").readlines():
        if start<i and i<=stop:
            data = syn.split(',')
            spec = data[4].replace('"','')
            if spec in seen.keys():
                lines[i]['col_id'] = seen[spec]
            else:
                lines[i] = {'name': spec,'col_id': None,'is_primary': -1,'walt_id':data[0]}
                cursor.execute ("SELECT record_id,is_species_or_nonsynonymic_higher_taxon FROM taxa WHERE name = '%s' LIMIT 1" % spec)
                res = cursor.fetchall()
                first = True
                for r in res:
                    lines[i]['col_id'] = r[0]
                    lines[i]['is_primary'] = r[1]
                    if not first:
                        lines[i]['is_primary'] = 2
                    first = False
                    seen[spec] = r[0]
        i+=1
    for l,p in lines.items():
        result_file.write("%s, %s, %s, %s\n" % (p['walt_id'],p['name'],p['col_id'],p['is_primary']))
    
                
if __name__ == "__main__":
    pipeline_run([SynOut], multiprocess = 1)
    pipeline_run([WaltOut], multiprocess = 1)
    synLog.write("%s, %s, %s, %s\n" % ("name","col-id","syn-name","syn-col-id"))
    waltLog.write("%s, %s, %s, %s\n" % ("walt-id","name","col-id","is-primary"))
    #for l,i in lines.items():
    #    synLog.write("%s, %s, %s, %s" % (i['name'],i['col_id'],i['syn_name'],i['syn_id']))
    for i in glob("*.syn"):
        synLog.write(open(i).read())
    for i in glob("*.walt"):
        waltLog.write(open(i).read())

