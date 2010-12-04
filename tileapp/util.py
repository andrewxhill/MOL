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
        while i < len(b):
            if col==0:
                a.append([])
            if b[i][3]!=0:
                tmp = '1'
            else:
                tmp = '0'
            a[row].append(tmp)
            col+=1
            if col==256:
                col = 0
                row+=1
            i+=1
        f = cStringIO.StringIO()
        palette=[(0xff,0xff,0xff,0x00),(0x00,0x00,0x00,0xff)]
        w = png.Writer(256,256, palette=palette, bitdepth=1)
        w.write(f, a)   
        
        return db.Blob(f.getvalue())
        
    return wrapper