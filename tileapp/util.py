from PIL import Image
from google.appengine.ext import db
import cStringIO
import png

def stdImg(fn):
    def wrapper(value):
        img = Image.open("%s.png" % value)   
        b = img.convert("RGBA").getdata()
        
        i = 0
        a = []
        col = 0
        row = 0
        fullTile = True
        while i < len(b):
            if col==0:
                a.append([])
            if b[i][3]!=0:
                a[row].append(0)
                a[row].append(0)
                a[row].append(0)
                a[row].append(255)
            else:
                a[row].append(0)
                a[row].append(0)
                a[row].append(0)
                a[row].append(0)
                fullTile = False
            col+=1
            if col==256:
                col = 0
                row+=1
            i+=1
        if fullTile:
            return db.Blob('f')
        else:
            f = cStringIO.StringIO()
            w = png.Writer(256,256, planes=4, alpha=True, greyscale=False, bitdepth=8)
            w.write_passes(f,a,packed=False)
            return db.Blob(f.getvalue())
        
    return wrapper
