# coding=utf-8

import configparser
import os

from defaultsettings import defaults


class Setting(object):
    pass


class SettingsManager(object):
    settings = {}

    @classmethod
    def _sanitize(cls, settings: Setting) -> Setting:
        # TODO : Check that settings that should be strings really are not lists
        # TODO : Check that audio languages conform to ISO standard
        # TODO : Substitute common aliases for codecs to get a clean list
        # In order to do that we need to cycle through the configuration sections. Find a way to do that.
        # Ideally, check that the setting is supported by ffmpeg
        # TODO : language should be its own section and should then be added to container settings

        pass

    @classmethod
    def FromFile(cls, settingsfile, name):

        if not os.path.isfile(settingsfile):
            raise Exception

        config = configparser.ConfigParser(converters={
            'list': lambda option: list(
                set(map(str.lower, option.strip().replace(" ", '').split(',')))) if option else [],
            'strlower': lambda option: option.lower() if option else None,
            'str': lambda option: option if option else None,
            'tryint': lambda option: int(option) if option.isnumeric() else 0,
            'tryfloat': lambda option: float(option) if option.isnumeric() else 0.0
        })

        config.read(settingsfile)
        settings = Setting()
        for section in defaults.keys():
            setattr(settings, section, Setting())

            for option in defaults[section].keys():
                optiontype = defaults[section][option][1]
                optionfb = defaults[section][option][0]
                subsetting = getattr(settings, section)
                if optiontype == 'str':
                    setattr(subsetting, option, config.getstr(section, option, fallback=optionfb))
                    continue
                elif optiontype == 'strlower':
                    setattr(subsetting, option, config.getstrlower(section, option, fallback=optionfb))
                    continue
                elif optiontype == 'list':
                    setattr(subsetting, option, config.getlist(section, option, fallback=optionfb))
                    continue
                elif optiontype == 'float':
                    setattr(subsetting, option, config.gettryfloat(section, option, fallback=optionfb))
                    continue
                elif optiontype == 'int':
                    setattr(subsetting, option, config.gettryint(section, option, fallback=optionfb))
                    continue
                elif optiontype == 'bool':
                    setattr(subsetting, option, config.getboolean(section, option, fallback=optionfb))
                    continue
                else:
                    raise Exception('Unsupported option type')

        cls.settings[name] = settings
        # TODO : Should we return separate settings objects for the different sections through a dict ?
        return settings

    def fromdict(self, request):  # TODO : implement
        pass

    def tofile(self, name, path: str):  # TODO : replace writedefaults with generic method to write to file
        pass

    @classmethod
    def getsettings(cls, name: str) -> Setting:
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


# SM = SettingsManager()
# SM.FromFile('/Users/Jon/Downloads/in/defaults.ini', 'defaults')

if __name__ == '__main__':
    path = '/Users/Jon/Downloads/in/'
    writedefaults(path)
