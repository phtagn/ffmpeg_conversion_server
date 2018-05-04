# coding=utf-8
from configobj import ConfigObj

from conftest import configdict

configspec = ConfigObj(configspec=configdict, list_values=False, encoding='UTF8', default_encoding='UTF8',
                       write_empty_values=True)

class SettingsManager(object):
    settings = {}

    @classmethod
    def fromfile(cls, configfile, name):
        settings = ConfigObj(configfile, configspec=configdict, encoding='UTF8', default_encoding='UTF8',
                             write_empty_values=True)
        cls.settings[name] = settings

    @classmethod
    def getsettings(cls, name):
        return cls.settings[name]


SM = SettingsManager()
SM.fromfile('config/defaults.ini', 'defaults')
