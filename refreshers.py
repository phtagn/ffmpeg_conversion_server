from __future__ import print_function

import logging
import os
import sys
from abc import ABCMeta, abstractmethod

import requests

from readSettings import ReadSettings

log = logging.getLogger(__name__)

class RefreshError(Exception):
    def __init__(self, name, url, error):

        super(RefreshError, self).__init__(error)

        self.url = url
        self.name = name
        self.error = error

    def __repr__(self):
        return ('<RefreshError {name} failed to refresh url {url}, error was: {err}>'.format(
            name=self.name, url=self.url, err=self.error))

    def __str__(self):
        return self.__repr__()


class RefresherFactory(object):
    Refreshers = {}


    @classmethod
    def register(cls, refresher):
        cls.Refreshers = {refresher.name: refresher}

    @classmethod
    def GetRefresher(cls, name, cfg):
        return cls.Refreshers[name](cfg['Refreshers'][name])


class Refresher(object):
    __metaclass__ = ABCMeta
    name = ''
    defaults = {'host': 'string(default=localhost)',
                'ssl': 'boolean(default=False',
                'webroot': 'string(default=None)',
                'refresh': 'boolean(default=False)'}

    @abstractmethod
    def refresh(self, param):
        pass


class SickRage(Refresher):
    name = 'Sickrage'
    defaultport = '8081'
    defaults = Refresher.defaults.copy()
    defaults.update({'port': 'integer(default=8081)',
                     'username': 'string(default=None)',
                     'password': 'string(default=None)',
                     'api_key': 'string(default=None)'
                     })

    def __init__(self, cfg):
        conf = cfg['Refreshers'][SickRage.name]
        self.host = conf.get('host')
        if conf.get('ssl'):
            self.protocol = 'https://'
        else:
            self.protocol = 'http://'
        self.port = cfg.get('port')
        self.username = cfg.get('username')
        self.password = cfg.get('password')

        if not cfg.get('webroot'):
            self.webroot = '/'
        elif cfg.get('webroot').endswith('/'):
            self.webroot = cfg.get('webroot')
        else:
            self.webroot = f'{cfg.get("webroot")}/'


        self.url = f'{self.protocol}{self.host}:{self.port}/{self.webroot}{self.api_key}'


    def refresh(self):
        if not self.apikey:
            raise RefreshError('Sickrage', '', 'Sickrage api key not defined')

        payload = {'cmd': 'show.refresh', 'tvdbid': showid}
        # + ":" + self.port
        url = self.protocol + self.host + self.web_root + "api/" + self.apikey + '/'

        try:
            r = requests.get(url, params=payload, stream=True, verify=True)
            if r.status_code != 200:
                raise Exception('Sickrage', 'url', r.status_code)
        except Exception as e:
            raise RefreshError('Sickrage', url, e.message)

        if r.json()['result'] == 'success':
            print('Refresh successful')
            return True


Refresher.register(SickRage)


class SickBeard(Refresher):
    name = 'Sickbeard'
    defaultport = 8081

    def __init__(self, settings):
        super(SickBeard, self).__init__(settings)
        self.username = getattr(settings, SickBeard.name)['user']
        self.password = getattr(settings, SickBeard.name)['pass']

    def refresh(self, showid):
        if not self.apikey:
            raise RefreshError('Sickbeard', '', 'Sickbeard api key not defined')

        import urllib
        url = self.protocol + self.host + ":" + self.port + self.web_root + "api/" + self.apikey + "/?cmd=show.refresh&tvdbid=" + str(
            showid)

        try:
            urllib.urlopen(url)
        except Exception as e:
            raise RefreshError('Sickbeard', url, e.message)


Refresher.register(SickBeard)


class Plex(Refresher):
    name = 'Plex'
    defaultport = 32400

    def __init__(self, settings):
        super(Plex, self).__init__(settings)
        self.token = getattr(settings, Plex.name).get('token', '')

    def refresh(self, param):
        if not self.token:
            raise RefreshError('Plex', '', 'Plex token not defined')

        from xml.dom import minidom
        base_url = '{protocol}{host}:{port}/library/sections'.format(protocol=self.protocol, host=self.host,
                                                                     port=self.port)
        refresh_url = '%s/%%s/refresh' % base_url
        payload = {'X-Plex-Token': self.token}
        try:
            r = requests.get(base_url, params=payload)
        except Exception as e:
            raise RefreshError('Plex', base_url, e.message)

        if r.status_code == 200:
            xml_sections = minidom.parseString(r.text)
            sections = xml_sections.getElementsByTagName('Directory')
            for s in sections:
                if s.getAttribute('type') == param:
                    r = requests.get(refresh_url % s.getAttribute('key'), payload)
                    if r.status_code == 200:
                        print("refresh successful")

Refresher.register(Plex)


class Sonarr(Refresher):
    name = 'Sonarr'
    defaultport = '8989'

    def __init__(self, settings):
        super(Sonarr, self).__init__(settings)

    def refresh(self, showid):
        pass


Refresher.register(Sonarr)

if __name__ == '__main__':
    rsettings = ReadSettings(os.path.dirname(sys.argv[0]), "autoProcess.ini")
    toto = Plex(rsettings)
    toto.refresh('80379')
