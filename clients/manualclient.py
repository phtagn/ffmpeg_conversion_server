#!/usr/bin/env python
import json
import sys
import xmlrpclib

""" This client connects to the mp4automator server to submit a conversion job. Note that the file being converted is 
NOT sent across. As a consequence, both the client and the server must have access to the file.
Important variables are :
SETTINGS : can be left blank, or can be pointed to an autoProcess.ini file that will be loaded by the server
PATHEQUIV : a dictionary containing the path relative to the client and the path relative to the server. 
PATHEQUIV is to be used when the client and server are running on different machines (or different docker containers). It can be left blank otherwise.
SERVER_ADDRESS: the address where the server is reachable.
"""

SERVER_ADDRESS = 'http://www.cholli.org:7080'

SETTINGS = '/config/manual.ini'

PATHEQUIV = {'/Volumes/Downloads': '/downloads',
             '/Volumes/video': '/video',
             '/Volumes/Films': '/films'}

s = xmlrpclib.Server(SERVER_ADDRESS)

inputfile = sys.argv[1]

request = {'params':
               {'jobtype': 'manual',
                'inputfile': inputfile,
                'original': ''
                }
           }

request['settings'] = SETTINGS
request['pathequiv'] = PATHEQUIV

try:
    request = json.dumps(request)
except:
    print('Could not create request')
    sys.exit()

try:
    print(s.convert(request, SETTINGS))
except xmlrpclib.Fault as err:
    print(err.faultString)
