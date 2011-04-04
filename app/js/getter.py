#!/usr/bin/env python

from optparse import OptionParser

def print_getters(properties):
    for p in properties:
        print '            get%s%s: function() {\n                return this._%s;\n            },' % (p[0].upper(), p[1:], p)

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-c", "--command", dest="command",
                      help="TGM command",
                      default=None)
    parser.add_option("-p", "--properties", dest="props",
                      help="Class properties",
                      default=None)

    (options, args) = parser.parse_args()
    command = options.command
    
    if command == 'getters':
        properties = options.props.split(',')
        print_getters(properties)

