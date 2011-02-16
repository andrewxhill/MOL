import httplib, urllib, shlex, simplejson


def queryCol(string):
    params = urllib.urlencode({'search': string, 'format': 'json', 'limit': 10})
    col = urllib.urlopen("http://mol-apps.appspot.com/api/taxonomy",params)
    return simplejson.load(col)['items']

def parseFile(fileName,logFile,nameCol=6, layerCol=0):
    log = open(logFile,"w+")
    ct = 0
    file = open(fileName,'r').read().split("\r\n")
    for line in file:
        if line.strip() != "":
            dat = line.split(",")
            data = []
            
            #respect enquoted columns
            cont = False
            for d in dat:
                d = d.strip()
                if cont:
                    data[-1] = data[-1] + "," + d
                else:
                    data.append(d)
                if len(d) > 0 and d.strip()[-1] == '"':
                    cont = False
                if len(d) > 0 and d.strip()[0] == '"':
                    cont = True
            name = None
            try:
                int(data[0])
                layer = "pas%s" % str(data[layerCol]) 
                name = str(data[nameCol]).strip().lower()
                
                ct+=1
            except:
                pass
            if name:
                col = queryCol(name)
                print name,col
                log.write("%s,%s,%s\n" %(layer,name,len(col)))
        
        

if __name__ == '__main__':
    logFile = "name_mapping.log"
    parseFile("NewSib20_HBWPass_short.txt",logFile)
         
