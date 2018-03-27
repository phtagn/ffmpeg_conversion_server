#!/usr/bin/env python
import json
import sys
import xmlrpclib

""" This client connects to the mp4automator server to submit a conversion job. Note that the file being converted is 
NOT sent across. As a consequence, both the client and the server must have access to the file.
Important variables are :
SETTINGS : can be left blank, or can be pointed to an autoProcess.ini file that will be loaded by the server
PATHEQUIV : a dictionary containing the path relative to the client and the path relative to the server. 
PATHEQUIV is to be used when the client and server are running on different machines (or different docker containers).
SERVER_ADDRESS: the address where the server is reachable.
"""

SERVER_ADDRESS = 'http://localhost:7080'
SETTINGS = '/config/sickrage.ini'
PATHEQUIV = {'/downloads': '/downloads/TvShows',
             '/tv': '/tv/Parents'}

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

    s = xmlrpclib.Server(SERVER_ADDRESS)

    try:
        print(s.convert(request, SETTINGS))
    except xmlrpclib.Fault as err:
        print(err.faultString)


else:
    print("Not enough command line arguments present %s." % len(sys.argv))
    sys.exit
