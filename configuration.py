from configobj import ConfigObj, Section
from configobj import flatten_errors
from typing import Union
import validate
import logging
from configuration.defaultconfig import configspec
import os
import languagecode

logging.basicConfig(filename='server.log', filemode='w', level=logging.DEBUG)
log = logging.getLogger(__name__)


class cfgmgr(object):
    def __init__(self):
        self._usercfg = None
        self._validator = validate.Validator()

        cfg = ConfigObj({},
                        configspec=configspec,
                        encoding='UTF8',
                        default_encoding='UTF8',
                        write_empty_values=True,
                        create_empty=True,
                        stringify=True)
        cfg.validate(self._validator, copy=True)
        self._defaultconfig = cfg

    @property
    def defaultconfig(self) -> ConfigObj:
        """
        Contains the default configuration
        """
        return self._defaultconfig

    def savedefaults(self):
        # self.defaultconfig.walk(self.nonetoempty)
        self._defaultconfig.filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config',
                                                    'defaults.ini')
        self._defaultconfig.write()

    @staticmethod
    def nonetoempty(section, key):
        val = section[key]
        newval = val
        if val is None:
            newval = ''

        section[key] = newval

    @property
    def cfg(self) -> ConfigObj:
        """
        Returns user complete user configuration
        """
        return self._usercfg

    def load(self, config: Union[str, dict], overrides=None):
        """
        Loads userconfig and validates it.
        """
        if overrides:
            override_settings = ConfigObj(overrides, configspec=configspec, encoding='UTF8', default_encoding='UTF8',
                                      write_empty_values=False)

            r = override_settings.validate(self._validator, preserve_errors=True)

            if isinstance(r, dict):
                log.error('Overrides contained errors, discarding')
                overrides = None

        inifile = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config', config)

        if os.path.exists(inifile):
            usersettings = ConfigObj(inifile, configspec=configspec, encoding='UTF8', default_encoding='UTF8',
                                     write_empty_values=True)
            output = ""
            if usersettings:

                if overrides:
                    usersettings.merge(overrides)

                r = usersettings.validate(self._validator, preserve_errors=True)

                if isinstance(r, dict):
                    raise ConfigException(output, self._usercfg)
                usersettings.walk(self.properNone)

                self._usercfg = usersettings
                self.fixafewthings()

        else:
            raise IOError(f'Could not find config file {inifile}')

    def fixafewthings(self):

        def getalias(codecnames: list) -> list:
            """
            Small function to fix some codecs being called by another name. For example, h265 is referred to as hevc.
            :param codecnames: name of a codec (e.g. h264, hevc)
            :return:
            """

            codecalias = {'h265': 'hevc',
                          'x264': 'h264',
                          'x265': 'hevc'}

            output = list(
                set([codecname if codecname not in codecalias else codecalias[codecname] for codecname in codecnames]))
            return output

        for section in self._usercfg['Containers']:

            # Make sure that vodecs are only mentionned once, and that there are no aliases the program would not understand

            self._usercfg['Containers'][section]['video']['accepted_track_formats'] = getalias(
                self._usercfg['Containers'][section]['video']['accepted_track_formats'])

            self._usercfg['Containers'][section]['audio']['accepted_track_formats'] = getalias(
                self._usercfg['Containers'][section]['audio']['accepted_track_formats'])

            self._usercfg['Containers'][section]['subtitle']['accepted_track_formats'] = getalias(
                self._usercfg['Containers'][section]['subtitle']['accepted_track_formats'])

            # Make sure that the transcode_to is also in accepted_track_formats
            if self._usercfg['Containers'][section]['video']['transcode_to'] not in \
                    self._usercfg['Containers'][section]['video']['accepted_track_formats']:
                self._usercfg['Containers'][section]['video']['accepted_track_formats'].append(
                    self._usercfg['Containers'][section]['video']['transcode_to'])

            if self._usercfg['Containers'][section]['audio']['transcode_to'] not in \
                    self._usercfg['Containers'][section]['audio']['accepted_track_formats']:
                self._usercfg['Containers'][section]['audio']['accepted_track_formats'].append(
                    self._usercfg['Containers'][section]['audio']['transcode_to'])

            # for audio only, make sure that the force_create_tracks are also on accepted track formats:
            for codec in self._usercfg['Containers'][section]['audio']['force_create_tracks']:

                if codec not in self._usercfg['Containers'][section]['audio']['accepted_track_formats']:
                    self._usercfg['Containers'][section]['audio']['accepted_track_formats'].append(codec)

        # Make sure that languages are in the correct ISO standard.
        for t in ['audio', 'subtitle']:
            self._usercfg['Languages'][t] = languagecode.validate(self._usercfg['Languages'][t])

    def extract_stream_config(self, typ):
        fmts = (self._usercfg['Containers'][typ]['video'].get('accepted_track_formats'),
                        [self._usercfg['Containers'][typ]['video'].get('transcode_to')],
                        self._usercfg['Containers'][typ]['audio'].get('accepted_track_formats'),
                        self._usercfg['Containers'][typ]['audio'].get('force_create_tracks'),
                        [self._usercfg['Containers'][typ]['audio'].get('transcode_to')],
                        self._usercfg['Containers'][typ]['subtitle'].get('accepted_track_formats'),
                        [self._usercfg['Containers'][typ]['subtitle'].get('transcode_to')])

        trackformats = []
        for fmt in fmts:
            trackformats.extend(fmt)

        trackformats = list(set(trackformats))

        r = {tfmt: self._usercfg['TrackFormats'][tfmt] for tfmt in trackformats}
        print(type(r))
        return r

    @staticmethod
    def properNone(section, key):
        val = section[key]
        newval = val
        if val == 'None' or 0:
            newval = None
        elif val == ['']:
            newval = []
        elif val == ['None']:
            newval = []

        section[key] = newval

    def save(self, name: str) -> bool:
        if self.cfg and name:
            self.cfg.filename = os.path.join('config', name + '.ini')
            self.cfg.write()
            return True

        return False


class ConfigException(Exception):
    def __init__(self, validator_output, config):
        error_message = ''
        for entry in flatten_errors(config, validator_output):
            section_list, key, value = entry
            error_message += f'Error in {":".join(section_list)}:{key}. This is very likely a key being ' \
                             f'specified with no value. Either set a value or remove the key.'

        self.message = error_message


if __name__ == '__main__':
#    toto = {'TrackFormats': {'theora': {'max_bitrate': '1080'}}}
    cm = cfgmgr()
    cm.savedefaults()
#    cm.load('defaults.ini', overrides=toto)
#    tf = cm.extract_stream_config('mp4')
#    print(tf)
