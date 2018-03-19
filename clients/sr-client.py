#!/usr/bin/env python
import json
import sys
import xmlrpclib

SETTINGS = {}
PATHEQUIV = {}
SERVER_ADDRESS = 'http://localhost:7080'
s = xmlrpclib.Server(SERVER_ADDRESS)

if len(sys.argv) > 4:
    inputfile = sys.argv[1]
    original = sys.argv[2]
    tvdb_id = int(sys.argv[3])
    season = int(sys.argv[4])
    episode = int(sys.argv[5])

    request = {'params':
                   {'jobtype': 'tvshow',
                    'inputfile': inputfile,
                    'original': original,
                    'tvdb_id': tvdb_id,
                    'season': season,
                    'episode': episode,
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
