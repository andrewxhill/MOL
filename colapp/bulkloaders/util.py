def create_key(value):
    return transform.create_deep_key(('Species', value), ('Species', transform.CURRENT_PROPERTY))

def toList(fn):
    def wrapper(value):
        #open('test.log', 'a').write("%s\n" % value.encode('utf-8'))
        #li = [x.strip() for x in value.split(',')]
        out = None
        if value is not None and len(value)>0 and eval(value):
            values = eval(value)
            out = values
            ct = 0
            while ct<len(values):
                v = values[ct].split()
                ct+=1
                if len(v) > 1:
                    for n in v:
                        out.append(n)
        else:
            out = None
        return out

    return wrapper
