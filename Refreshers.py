from __future__ import print_function

import logging
import os
import sys
from abc import ABCMeta, abstractmethod

import requests

from readSettings import ReadSettings


class RefreshError(Exception):
    def __init__(self, name, url, error):
        """
        @param    name: Name of the refresher.
        @type     name: C{str}

        @param    url: Full url that was used.
        @type     req: C{str}

        @param    error: Error that was raised.
        @type     error: C{str}
        """
        super(RefreshError, self).__init__(error)

        self.url = url
        self.name = name
        self.error = error

    def __repr__(self):
        return ('<RefreshError {name} failed to refresh url {url}, error was: {err}>'.format(
            name=self.name, url=self.url, err=self.error))

    def __str__(self):
        return self.__repr__()


def GetRefresher(name, settings):
    if name == 'sickrage':
        return SickRage(settings)
    if name == 'sonarr':
        pass
    if name == 'radar':
        pass
    if name == 'sickbeard':
        return SickRage(settings)
    if name == 'couchpotato':
        pass
    if name == 'plex':
        return Plex(settings)


class Refresher(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(self, settings, logger=None):
        """Import settings common to all refreshers"""
        assert isinstance(settings, ReadSettings)

        if logger:
            self.log = logger
        else:
            self.log = logging.getLogger(__name__)

        self.protocol = 'http://'
        self.host = getattr(settings, self.__class__.name).get('host', 'localhost')
        self.port = getattr(settings, self.__class__.name).get('port', self.__class__.defaultport)

        if getattr(settings, self.__class__.name).get('ssl', False):
            self.protocol = 'https://'

        self.web_root = getattr(settings, self.__class__.name).get('web_root', "")

        if not self.web_root.startswith("/"):
            self.web_root = "/" + self.web_root
        if not self.web_root.endswith("/"):
            self.web_root = self.web_root + "/"

        # Readsettings sometimes references apikey with an underscore
        try:
            self.apikey = getattr(settings, self.__class__.name)["api_key"]
        except KeyError:
            pass

        try:
            self.apikey = getattr(settings, self.__class__.name)["apikey"]
        except KeyError:
            pass

    @abstractmethod
    def refresh(self, param):
        pass


class SickRage(Refresher):
    name = 'Sickrage'
    defaultport = '8081'

    def __init__(self, settings):
        super(SickRage, self).__init__(settings)
        self.username = getattr(settings, SickRage.name)['user']
        self.password = getattr(settings, SickRage.name)['pass']

    def refresh(self, param):
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
        super(SickRage, self).__init__(settings)
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


00120
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
