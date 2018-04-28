#!/usr/bin/env python
import json
import sys

import xmlrpclib

SETTINGS = {}
PATHEQUIV = {}
SERVER_ADDRESS = 'http://localhost:7080'
s = xmlrpclib.Server(SERVER_ADDRESS)

if len(sys.argv) > 3:
    imdbid = sys.argv[1]
    inputfile = sys.argv[2]
    original = sys.argv[3]

    request = {'params':
                   {'jobtype': 'movie',
                    'inputfile': inputfile,
                    'original': original,
                    'imdb_id': imdbid
                    }
               }

    request['settings'] = SETTINGS
    request['pathequiv'] = PATHEQUIV

    try:
        request = json.dumps(request)
    except:
        print('Could not create request')
        sys.exit()

    print(s.convert(request))
else:
    print("Not enough command line arguments present %s." % len(sys.argv))
    sys.exit
