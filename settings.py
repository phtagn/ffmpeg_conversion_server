# coding=utf-8

import configparser
import os

from defaultsettings import defaults


class Setting(object):
    pass


class SettingsManager(object):
    settings = {}

    @classmethod
    def FromFile(cls, settingsfile, name):

        if not os.path.isfile(settingsfile):
            raise Exception

        config = configparser.ConfigParser(converters={
            'list': lambda option: list(set(map(str.lower, option.strip().replace(" ", '').split(',')))),
            'strlower': lambda option: option.lower().strip(),
            'str': lambda option: option.strip(),
            'tryint': lambda option: int(option) if option.isnumeric() else 0,
            'tryfloat': lambda option: float(option) if option.isnumeric() else 0.0
        })

        config.read(settingsfile)
        parent = Setting()
        for section in defaults.keys():
            setattr(parent, section, Setting())

            for option in defaults[section].keys():
                optiontype = defaults[section][option][1]
                optionfb = defaults[section][option][0]
                child = getattr(parent, section)
                if optiontype == 'str':
                    setattr(child, option, config.get(section, option, fallback=optionfb))
                    continue
                elif optiontype == 'strlower':
                    setattr(child, option, config.getstrlower(section, option, fallback=optionfb))
                    continue
                elif optiontype == 'list':
                    setattr(child, option, config.getlist(section, option, fallback=optionfb))
                    continue
                elif optiontype == 'float':
                    setattr(child, option, config.gettryfloat(section, option, fallback=optionfb))
                    continue
                elif optiontype == 'int':
                    setattr(child, option, config.gettryint(section, option, fallback=optionfb))
                    continue
                elif optiontype == 'bool':
                    setattr(child, option, config.getboolean(section, option, fallback=optionfb))
                    continue
                else:
                    raise Exception('Unsupported option type')

        cls.settings[name] = parent

        return parent

    def fromdict(self, request):
        pass

    def tofile(self, name, path: str):
        pass

    @classmethod
    def getsettings(cls, name):
        return cls.settings[name]


def writedefaults(path: str):
    """
    Writes default configuration values to default.ini
    """
    # TODO validate write access to path
    config = configparser.ConfigParser()
    for section in defaults.keys():
        config[section] = {}
        for option in defaults[section].keys():
            config[section][option] = str(defaults[section][option][0])

    with open(os.path.join(path, 'defaults.ini'), 'w') as configfile:
        config.write(configfile)

    return True


SM = SettingsManager()
SM.FromFile('/Users/Jon/Downloads/in/defaults.ini', 'default')

if __name__ == '__main__':
    path = '/Users/Jon/Downloads/in/'
    writedefaults(path)
