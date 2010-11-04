def create_key(value):
    return transform.create_deep_key(('Species', value), ('Species', transform.CURRENT_PROPERTY))

def toList(fn):
    def wrapper(value):
        #open('test.log', 'a').write("%s\n" % value.encode('utf-8'))
        li = [x.strip() for x in value.split(',')]
        out = {}
        for l in li:
            out[l] = 1
            l = l.split(" ")
            if len(l) > 1:
                for w in l:
                    out[w] = 1
        return out.keys()
        
    return wrapper
