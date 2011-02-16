zoom = 10
out = open('data10.csv',"w+")
layerid = '1010'

def qt( x, y, z ):
    q = ""
    #y = ((1 << z) - y - 1)
    i = z;
    while (i > 0):
        digit = 0;
        mask = 1 << (i-1)
        if (x & mask) != 0:
            digit+=1
        if (y & mask) != 0:
            digit = digit + 2
        q = q + str(digit)
        i=i-1
    print q
    return q
    
f = open('output.log')
out.write("key,file,updatekey\n")
for l in f.readlines():
    d = l.split(' ')
    if len(d)>2:
        p = d[2]
        a = p.split('/')
        if len(a)==4:
            z = int(a[1].replace('z',''))
            if z==zoom:
                x = int(a[2])
                y = int(a[3].split('.')[0])
                q = qt(x,y,z)
                key = "%s/%s/pa" % (layerid,q)
                update = "%s/%s/pa" % (layerid,q[0:-1])
                out.write("%s,%s,%s\n" % (key,p.split('.')[0],update))
