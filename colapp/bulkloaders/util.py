def create_key(value):
    return transform.create_deep_key(('Species', value), ('Species', transform.CURRENT_PROPERTY))

def toList(fn):
    def wrapper(value):
        #open('test.log', 'a').write("%s\n" % value.encode('utf-8'))
        return [x.strip() for x in value.split(',')]
    return wrapper
