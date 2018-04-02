from __future__ import print_function

import os
import sys
from abc import ABCMeta, abstractmethod

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
        return ('<RefreshError {name} failed to refresh url {url}, error was {err}>'.format(
            name=self.name, url=self.url, err=self.error))

    def __str__(self):
        return self.__repr__()


def GetRefresher(name):
    if name == 'sickrage':
        return True
    if name == 'sonarr':
        pass
    if name == 'radar':
        pass
    if name == 'sickbeard':
        pass
    if name == 'couchpotato':
        pass
    if name == 'plex':
        pass


class Refresher(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(self, settings):
        """Import settings common to all refreshers"""
        assert isinstance(settings, ReadSettings)

        self.host = getattr(settings, self.__class__.name)["host"]
        self.port = getattr(settings, self.__class__.name)["port"]

        try:
            ssl = getattr(settings, self.__class__.name)["ssl"]
        except:
            ssl = False

        if ssl:
            self.protocol = 'https://'
        else:
            self.protocol = 'http://'

        self.web_root = getattr(settings, self.__class__.name).get("web_root", "")

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
    def getURL(self, showid):
        pass

    @abstractmethod
    def refresh(self, params):
        pass


class SickRage(Refresher):
    name = 'Sickrage'

    def __init__(self, settings):
        super(SickRage, self).__init__(settings)
        self.username = getattr(settings, SickRage.name)['user']
        self.password = getattr(settings, SickRage.name)['pass']

    def getURL(self, showid):
        pass

    def refresh(self, showid):
        import urllib
        url = self.protocol + self.host + ":" + self.port + self.web_root + "/api/" + self.apikey + "/?cmd=show.refresh&tvdbid=" + showid
        try:
            urllib.urlopen(url)
        except Exception as e:
            raise RefreshError('Sickrage', url, e.message)


Refresher.register(SickRage)


class SickBeard(Refresher):
    name = 'Sickbeard'

    def __init__(self, settings):
        super(SickBeard, self).__init__(settings)

    def getURL(self, showid):
        pass

    def refresh(self, showid):
        import urllib
        url = self.protocol + self.host + ":" + self.port + self.web_root + "/api/" + self.apikey + "/?cmd=show.refresh&tvdbid=" + showid
        try:
            urllib.urlopen(url)
        except Exception as e:
            raise RefreshError('Sickbeard', url, e.message)


Refresher.register(SickBeard)


class Plex(Refresher):
    name = 'Plex'

    def __init__(self, settings):
        super(Plex, self).__init__(settings)
        self.dorefresh = getattr(settings, Plex.name)['refresh']
        self.tokeb = getattr(settings, Plex.name)['token']

    def refresh(self, showid):
        pass


class Sonarr(Refresher):
    pass


Refresher.register(Sonarr)

if __name__ == '__main__':
    settings = ReadSettings(os.path.dirname(sys.argv[0]), "autoProcess.ini")
    toto = SickRage(settings)
    print(toto.__dict__)
