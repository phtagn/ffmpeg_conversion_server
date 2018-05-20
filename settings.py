# coding=utf-8
from configobj import ConfigObj
from validate import Validator

from converter.avcodecs import codec_dict

from defaultconfig import defaultconfig


class SettingsManager(object):
    settings = {}

    @classmethod
    def fromfile(cls, configfile, name):
        settings = ConfigObj(configfile, encoding='UTF8', default_encoding='UTF8', write_empty_values=True)
        cls.settings[name] = settings

    @classmethod
    def getsettings(cls, name):
        return cls.settings[name]


SM = SettingsManager()
SM.fromfile('config/defaults.ini', 'defaults')

conf = ConfigObj(defaultconfig, encoding='UTF8', default_encoding='UTF8', write_empty_values=True, create_empty=True)
conf.filename = 'config/testouille.ini'
conf.write()