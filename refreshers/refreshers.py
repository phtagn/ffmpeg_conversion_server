from __future__ import print_function
import os
import sys
from abc import ABCMeta, abstractmethod
import requests
import logging


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


class Refresher(metaclass=ABCMeta):
    name = ''
    defaults = {'host': 'string(default=localhost)',
                'ssl': 'boolean(default=False',
                'webroot': 'string(default=None)',
                'refresh': 'boolean(default=False)'}


    @abstractmethod
    def refresh(self, param):
        pass


class SickRage(Refresher):
    name = 'sickrage'
    defaultport = '8081'
    defaults = Refresher.defaults.copy()
    defaults.update({'port': 'integer(default=8081)',
                     'api_key': 'string(default=None)'
                     })

    def __init__(self, **kwargs):
        essential = ['api_key', 'host', 'port']
        self.api_key = None
        self.host = None
        self.port = None

        for k in essential:
            try:
                setattr(self, k, kwargs[k])
            except:
                raise Exception(f'{" ,".join(essential)} not present')

        if 'ssl' in kwargs:
            self.protocol = 'https://'
        else:
            self.protocol = 'http://'


        if kwargs.get('webroot', None):
            if kwargs['webroot'].endswith('/'):
                self.webroot = kwargs['webroot']
            else:
                self.webroot = f'{kwargs["webroot"]}/'
        else:
            self.webroot = '/'

        self.url = f'{self.protocol}{self.host}:{self.port}{self.webroot}api/{self.api_key}'


    def refresh(self, showid):
        if not self.api_key:
            raise RefreshError('Sickrage', '', 'Sickrage api key not defined')

        payload = {'cmd': 'show.refresh', 'tvdbid': showid}

        try:
            r = requests.get(self.url, params=payload, stream=True, verify=True)
            if r.status_code != 200:
                raise Exception('Sickrage', 'url', r.status_code)
        except Exception as e:
            raise RefreshError('Sickrage', self.url, e.message)

        if r.json()['result'] == 'success':
            print('Refresh successful')
            return True


class Plex(Refresher):
    name = 'plex'

    def __init__(self, **kwargs):
        essential = ['token', 'host', 'port']
        self.token = None
        self.host = None
        self.port = None

        for k in essential:
            try:
                setattr(self, k, kwargs[k])
            except:
                raise Exception(f'{" ,".join(essential)} not present')

        try:
            if kwargs['ssl'] is True:
                self.protocol = 'https://'
            else:
                self.protocol = 'http://'
        except KeyError:
            self.protocol = 'http://'

        if kwargs.get('webroot', None):
            if kwargs['webroot'].endswith('/'):
                self.webroot = kwargs['webroot']
            else:
                self.webroot = f'{kwargs["webroot"]}/'
        else:
            self.webroot = '/'

        self.url = f'{self.protocol}{self.host}:{self.port}{self.webroot}library/sections'

    def refresh(self, refresh_what: str):
        """
        :param refresh_what: str, can be 'movie' or 'show
        :return: None
        """


        from xml.dom import minidom

        refresh_url = '%s/%%s/refresh' % self.url
        payload = {'X-Plex-Token': self.token}

        try:
            r = requests.get(self.url, params=payload)
        except Exception as e:
            raise RefreshError('Plex', self.url, e.message)

        if r.status_code == 200:
            xml_sections = minidom.parseString(r.text)
            sections = xml_sections.getElementsByTagName('Directory')
            for s in sections:
                m = s.getAttribute('type')
                if m == refresh_what:
                    r = requests.get(refresh_url % s.getAttribute('key'), payload)
                    if r.status_code == 200:
                        print("refresh successful")


class RefresherFactory(object):
    Refreshers = {'sickrage': SickRage, 'plex': Plex}

    @classmethod
    def get_refesher(cls, name, **kwargs):
        for r in cls.Refreshers:
            if cls.Refreshers[r].name == name:
                return cls.Refreshers[name](**kwargs)
        raise Exception('Refresher not supported at this time')

if __name__ == '__main__':
    host = 'router.cholli.org'

    srs = {'api_key': '3aaff65b7087dfebc0ef3c6b691d6ee8', 'host': host, 'ssl': True, 'webroot': '/sickrage', 'port': 443}
    SR = RefresherFactory.get_refesher('sickrage', **srs)
    SR.refresh(75978)

    plex = {'token': '2dhXxPdwHiztGtGXjHBS', 'host': host, 'port': 32400, 'ssl': True}
    PL = RefresherFactory.get_refesher('plex', **plex)
    PL.refresh('movie')