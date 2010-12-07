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
                a[row].append(0)
                a[row].append(0)
                a[row].append(0)
                a[row].append(255)
            else:
                a[row].append(0)
                a[row].append(0)
                a[row].append(0)
                a[row].append(0)
            col+=1
            if col==256:
                col = 0
                row+=1
            i+=1
        f = cStringIO.StringIO()
        
        w = png.Writer(256,256, planes=4, alpha=True, greyscale=False, bitdepth=8)
        #w.write_array(f,n)
        w.write_passes(f,a,packed=False)
        """
        palette=[(0x00,0x00,0x00,0x00),(0x00,0x00,0x00,0xff)]
        #palette=[(0,0,0,0),(0,0,0,255)]
        w = png.Writer(256,256, interlace=0, palette=palette, bitdepth=1, greyscale=False)
        w.write(f, a)   
        """
        
        return db.Blob(f.getvalue())
        
    return wrapper
