import json
import sys
import xmlrpclib

if __name__ == '__main__':
    ep1 = {
        'params': {
            'jobtype': 'tvshow',
            'inputfile': '/downloads/Fargo S02E01.mkv',
            'original': '/downloads/Fargo S02E01.mkv',
            'season': 2,
            'episode': 1,
            'tvdb_id': '269613'
        }
    }

    SETTINGS = {'tagfile': 'True',
                'ffmpeg': '/usr/bin/ffmpeg',
                'ffprobe': '/usr/bin/ffprobe'}

    # PATHEQUIV = {'/Users/Jon/Downloads/meuh': '/Users/Jon/Downloads/in'}
    PATHEQUIV = {}

    if SETTINGS:
        ep1['settings'] = SETTINGS

    ep1['pathequiv'] = PATHEQUIV

    SERVER_ADDRESS = 'http://localhost:7080'
    s = xmlrpclib.Server(SERVER_ADDRESS)

    try:
        request = json.dumps(ep1)
    except Exception as e:
        print(e)
        print('Could not create request')
        sys.exit()

    print(s.convert(request))
