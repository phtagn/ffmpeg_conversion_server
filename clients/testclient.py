import json
import sys

import xmlrpclib

if __name__ == '__main__':
    ep1 = {
        'params': {
            'jobtype': 'tvshow',
            'inputfile': '/Users/Jon/Downloads/in/Fargo S02E01.mkv',
            'original': '/downloads/Fargo S02E01.mkv',
            'season': 2,
            'episode': 1,
            'tvdb_id': '269613'
        }
    }

    ep2 = {
        'params': {
            'jobtype': 'tvshow',
            'inputfile': '/downloads/Fargo S02E02.mkv',
            'original': '/downloads/Fargo S02E02.mkv',
            'season': 2,
            'episode': 2,
            'tvdb_id': '269613'
        }
    }

    PATHEQUIV = {}
    SETTINGS = '/Users/Jon/Downloads/config/localsettings.ini'
    # SETTINGS = '/config/testsettings.ini'
    ep1['pathequiv'] = PATHEQUIV
    ep2['pathequiv'] = PATHEQUIV

    SERVER_ADDRESS = 'http://localhost:7080'
    s = xmlrpclib.Server(SERVER_ADDRESS)

    try:
        request = json.dumps(ep1)
    except Exception as e:
        print(e)
        print('Could not create request')
        sys.exit()

    result = 'toto'
    try:
        result = s.convert(request, SETTINGS)
    except xmlrpclib.Fault as err:
        print('Error: %s' % err.faultString)

    print(result)

#    try:
#        print(s.loadsettings('/config/removesettings.ini'))
#    except:
#        print('Could not load settings or default settings')
#        sys.exit(1)

#    try:
#        request2 = json.dumps(ep2)
#    except Exception as e:
#        print(e)
#        print('Could not create request')
#        sys.exit()

#    print(s.convert(request2))
