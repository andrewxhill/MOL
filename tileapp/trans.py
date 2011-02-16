
def qt(x,y,z):
    i = 1
    last = 0
    div = (1 << (z-1))
    q = ''
    while i<=z:
        m = (1 << (i-1))
        d = div/m #256
        if last in [1,3]:
            x = x - 2*d #415
        if last in [2,3]:
            y = y - 2*d #305
        c = 0
        if x > d-1: c = c+1 
        if y > d-1: c = c+2 
        q += str(c)
        last = c
        i+=1
    return q
