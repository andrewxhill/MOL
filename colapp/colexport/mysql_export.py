# -*- coding: utf-8 -*-

import MySQLdb, re, codecs
import simplejson, sys

conn = MySQLdb.connect (host = "localhost",
                       port = 3306,
                       user = "username",
                       passwd = "password",
                       db = "col2010ac")
                       
specindQ = open("colexport/specind-quarantine.csv","w+")
bulk = open("upload.sh","w+")

def fix_latin(z):
    r= []
    c = 0
    while c<len(z):
        if type(z[c]) == type(str()):
            r.append(unicode(z[c],'latin-1').encode("utf-8"))
        else:
            r.append(z[c])
        c+=1
    return r
    
def cs(val,lower=1,quote=1): #clean the string from some weird junk in some of the fields
    if val==None or val=='None':
        return "NULL"
    if lower==1:
        val = val.replace('"','').replace("\n","").replace("'","''").strip("'").strip().lower()
    else:
        val = val.replace('"','').replace("\n","").replace("'","''").strip("'").strip()
    if quote==1:
        return "'" + val + "'"
    return val
    
def run():
    fnum = 0
    rct = 0
    specindN = open("colexport/specind-%s.csv" % fnum,"w+")
    specindN.write("record_id\tkey\tname_code\tcol_lsid\tdatabase_full_name\trank\tname\tkingdom\tphylum\tclassx\torderx\tfamily\tsuperfamily\tgenus\tspecies\tinfraspecies\tauthor\tnameslist\tnamesjson\tclassification\tauthorityDetails\tauthority\n")
    specindQ.write("record_id\tkey\tname_code\tcol_lsid\tdatabase_full_name\trank\tname\tkingdom\tphylum\tclassx\torderx\tfamily\tsuperfamily\tgenus\tspecies\tinfraspecies\tauthor\tnameslist\tnamesjson\tclassification\tauthorityDetails\tauthority\n")
    bulk.write("../../../google_appengine/appcfg.py upload_data --batch_size=25 --config_file=bulkloaders/col-mol.yaml --filename=colexport/specind-%s.csv --kind=Species  ../app/\n" % fnum)
    bulk.write("../../../google_appengine/appcfg.py upload_data --batch_size=25 --config_file=bulkloaders/col-mol.yaml --filename=colexport/specind-%s.csv --kind=SpeciesIndex  ../app/\n" % fnum)

    cursor = conn.cursor ()
    """
    cursor.execute ("CREATE TABLE spec (record_id INT, keyx TEXT, name_code TEXT, col_lsid TEXT, database_full_name TEXT, rank TEXT, name TEXT, kingdom TEXT, phylum TEXT, classx TEXT, orderx TEXT, family TEXT, superfamily TEXT, genus TEXT, species TEXT, infraspecies TEXT, author TEXT);")
    cursor.execute ("SELECT s.record_id,lsid,taxon,kingdom,phylum,class,f.order,family,superfamily,genus,species, infraspecies, author,database_full_name,s.name_code FROM scientific_names s,taxa t, `databases` d,families f WHERE s.is_accepted_name = 1 AND f.is_accepted_name=1 AND s.database_id = d.record_id AND s.family_id = f.record_id AND t.record_id = s.record_id AND t.is_accepted_name = 1 AND upper(kingdom) = 'ANIMALIA';")
    data = cursor.fetchall()
    for r in data:
        #pattern = u'[^\.a-z -]'
        if r[11] is None or len(r[11].strip())==0:
            key = "'animalia/%s/%s_%s'" % (cs(r[2],1,0), cs(r[9],1,0),cs(r[10],1,0))
        else:
            key = "'animalia/%s/%s_%s_%s'" % (cs(r[2],1,0), cs(r[9],1,0),cs(r[10],1,0),cs(r[11],1,0))
        key = key.rstrip(',')
        if "," in key: #some COL rows have concatenated name/author but are really duplicates of correct rows. remove them here
            print key
        else:                                         
            sql = 'INSERT INTO spec (record_id, col_lsid, rank, kingdom, phylum, classx, orderx, family, superfamily, genus, species, infraspecies, author, database_full_name,name_code,keyx) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);' % (r[0], cs(r[1]), cs(r[2]), cs(r[3]), cs(r[4]), cs(r[5]), cs(r[6]), cs(r[7]), cs(r[8]), cs(r[9]), cs(r[10]), cs(r[11]), cs(r[12],0).lstrip('(').rstrip(')'), cs(r[13],0), cs(r[14],0), key)
            #print sql
            cursor.execute(sql)
    """
    print "table made"
    cursor.execute ("SELECT * FROM spec;") # WHERE genus = 'Cosmosatyrus';")
    data = cursor.fetchall ()
    totalCount = 0
    for z in data:
        
        rct+=1
        
        if rct==10000:
            fnum+=1
            specindN.close()
            specindN = open("colexport/specind-%s.csv" % fnum,"w+")
            specindN.write("record_id\tkey\tname_code\tcol_lsid\tdatabase_full_name\trank\tname\tkingdom\tphylum\tclassx\torderx\tfamily\tsuperfamily\tgenus\tspecies\tinfraspecies\tauthor\tnameslist\tnamesjson\tclassification\tauthorityDetails\tauthority\n")
            bulk.write("../../../google_appengine/appcfg.py upload_data --batch_size=25 --config_file=bulkloaders/col-mol.yaml --filename=colexport/specind-%s.csv --kind=Species  ../app/\n" % fnum)
            bulk.write("../../../google_appengine/appcfg.py upload_data --batch_size=25 --config_file=bulkloaders/col-mol.yaml --filename=colexport/specind-%s.csv --kind=SpeciesIndex  ../app/\n" % fnum)
            rct=0
        
        r = fix_latin(z)
        
        names = []
        namesdicts = []
        cursor.execute ('SELECT c.common_name,c.language FROM common_names c WHERE name_code = "%s";' % r[2])
        cn = cursor.fetchall ()
        for p in cn:
            n = fix_latin(p)
            names.append(cs(n[0],1,0))
            namesdicts.append({
                "name":cs(n[0],0,0),
                "language":cs(n[1],0,0),
                "type":"common name",
                "author": None,
                "source": "COL",
                })
            
        charFlag = False
        cursor.execute ('SELECT s.genus,s.species,s.infraspecies,s.is_accepted_name,author FROM scientific_names s where accepted_name_code = "%s";' % r[2])
        sn = cursor.fetchall ()
        for p in sn:
            
            n = fix_latin(p)
            #n = p
            if n[2] is None or len(n[2])==0:
                nm = "%s %s" % (cs(n[0],1,0),cs(n[1],1,0))
                nmu = "%s %s" % (cs(n[0],0,0),cs(n[1],0,0))
            else:
                nm = "%s %s %s" % (cs(n[0],1,0),cs(n[1],1,0),cs(n[2],1,0))
                nmu = "%s %s %s" % (cs(n[0],0,0),cs(n[1],0,0),cs(n[2],0,0))
            names.append(nm)
            nd = {"name":nmu,"language":"latin"}
            auth = n[4]
            if auth is not None:
                auth = n[4].strip().lstrip("(").rstrip(")")
            nd["author"]=auth
            if n[3] == 1:
                nd["type"]="accepted name"
            else:
                nd["type"]="scientific name"
            nd["source"] = "COL"
            namesdicts.append(nd)  
        if r[16] is not None and type(r[16]) != type(None):
            r[16] = r[16].strip().lstrip("(").rstrip(")")
        taxonomy = {
                "kingdom": r[7],
                "phylum": r[8],
                "class": r[9],
                "order": r[10],
                "family": r[11],
                "superfamily": r[12], 
                "genus": r[13], 
                "species": r[14],
                "infraspecies": None}
                
        if r[16] is not None and type(r[16]) != type(None):
            taxonomy["author"] = r[16].strip().lstrip("(").rstrip(")")
        if r[15] is not None:
            taxonomy["infraspecies"] = r[15]
            
        authority = {"authority": "COL",
                     "database": r[4],
                     "external identifier": r[3]
                     }
        
        """
        tmps = sys.getsizeof(r[1]) 
        if tmps > 77:
            print tmps, r[1]
            specind = specindL
        else:
            specind = specindS
        
        if r[0] in [3355466,3353868,958299,965444,958495,969162,962838,958073]:
            specind = specindA
        """
        try:
            u"%s" % (r[1])
            specind = specindN
        except:
            print repr(r[1])
            specind = specindQ
        try:
            int(r[0])
        except:
            specind = specindQ
            print "You probably have a linebreak in a cell. Do a text search on '%s' to find it." % r[1]
            
        for i in r:
            if i is None:
                specind.write('')
            else:
                specind.write("%s" % i)
                
            specind.write("\t")  
        specind.write(simplejson.dumps(names).replace("\\/","/"))
        specind.write("\t")
        specind.write(simplejson.dumps(namesdicts).replace("\\/","/"))
        specind.write("\t")
        specind.write(simplejson.dumps(taxonomy).replace("\n","").replace("\r","").replace("\\/","/"))
        specind.write("\t")
        specind.write(simplejson.dumps(authority).replace("\\/","/"))
        specind.write("\t")
        specind.write('COL')
        specind.write("\n")
        totalCount += 1
    cursor.close ()
    print 'TotalCount: %s' % totalCount
    

if __name__ == "__main__":
    run()
