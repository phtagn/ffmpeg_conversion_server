import configuration
from converter.optionbuilder import OptionBuilder
from converter.containers import ContainerFactory, Container
from converter.streams import AudioStream
from converter.streamoptions import *
import os
import sys
from converter.encoders import EncoderFactory, Encoders
import logging
from converter.ffmpeg import FFMpeg

log = logging.getLogger()
log.setLevel(logging.DEBUG)
sh = logging.StreamHandler(sys.stdout)
sh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)s - %(message)s')
sh.setFormatter(formatter)
log.addHandler(sh)
# log = logging.getLogger(__name__)

"""Processes a video file in steps:
1) Analyse video file
2) Assess appropriate streams from options
3) Build templates from options
4) Build option list
5) Convert !
"""


class ProcessorConfig(object):
    def __init__(self, config, target):
        self.config = config
        self.target = target

        self._audio_languages = [Language(lng) for lng in self.config['Languages']['audio']]
        self._subtitle_languages = [Language(lng) for lng in self.config['Languages']['subtitle']]

        self.ffmpeg = FFMpeg(self.config['FFMPEG']['ffmpeg'], self.config['FFMPEG']['ffprobe'])
        self.ignore = {'video': self.config['Containers'][self.target]['video'].get('prefer_copy', False),
                       'audio': self.config['Containers'][self.target]['audio'].get('prefer_copy', False),
                       'subtitle': self.config['Containers'][self.target]['subtitle'].get('prefer_copy', False)}

        self.audio_create_tracks = self.config['Containers'][self.target]['audio']['force_create_tracks']

        self._defaults = self.load_defaults()
        self.program_encoders = Encoders(self.ffmpeg)
        self._stream_formats = self.load_stream_formats()
        self.encoders_defaults = self.load_encoders()
        self.preferred_encoders = self.config['PreferredEncoders']
        self.encoder_factory = EncoderFactory(self.program_encoders, self.encoders_defaults, self.preferred_encoders)
        self.preopts = self.config['Containers'][self.target]['preopts']
        self.postopts = self.config['Containers'][self.target]['postopts']

    @property
    def defaults(self):
        return self._defaults

    @property
    def stream_formats(self):
        return self._stream_formats

    @property
    def audio_languages(self):
        return self._audio_languages

    @property
    def subtitle_languages(self):
        return self._subtitle_languages

    def load_defaults(self):
        defaults = {}
        for k in ['audio', 'video', 'subtitle']:
            _options = Options()
            try:
                _codec = self.config['Containers'][self.target][k]['default_format']
            except IndexError:
                log.critical('There are no default options in accepted_track_formats')
                raise Exception('No default options')

            if _codec in self.config['StreamFormats']:
                for opt_name, opt_value in self.config['StreamFormats'][_codec].items():
                    option = OptionFactory.get_option(opt_name)
                    if option:
                        if isinstance(opt_value, list) and len(opt_value) > 0:
                            _options.add_option(option(opt_value[0]))
                        else:
                            _options.add_option(option(opt_value))

            if _options:
                defaults.update({k: (Codec(_codec), _options)})

        return defaults

    def load_stream_formats(self):

        templates = {}
        for k in ['video', 'audio', 'subtitle']:

            for _codec in self.config['Containers'][self.target][k].get('accepted_track_formats', []):
                if _codec in self.config['StreamFormats']:
                    _options = Options()

                    for opt_name, opt_value in self.config['StreamFormats'][_codec].items():
                        option = OptionFactory.get_option(opt_name)
                        if option:
                            if isinstance(opt_value, list):
                                for v in opt_value:
                                    _options.add_option(option(v))
                            else:
                                _options.add_option(option(opt_value))
                    templates.update({Codec(_codec): _options})

        return templates

    def load_encoders(self):

        encs = {}

        for encoder in self.program_encoders.supported_codecs:

            _options = Options()
            if encoder.codec_name in self.config['EncoderOptions']:
                for k, v in self.config['EncoderOptions'][encoder.codec_name].items():
                    _option = OptionFactory.get_option(k)
                    if _option:
                        _options.add_option(_option(v))

            encs[encoder.codec_name] = _options

        return encs


class Processor(object):

    def __init__(self, config, inputfile, outputfile, target, explode=False):
        """
        Creates a target source_container from the inputfile, taking into account the configuration
        :param config: a configuration object
        :type config: ConfigObj
        :param inputfile: path to the input file
        :type inputfile: os.path.abspath
        :param target: the target source_container to create
        :type target: str
        """
        self.config = ProcessorConfig(config, target)
        if os.path.exists(inputfile):
            self.infile = inputfile
        else:
            raise FileNotFoundError
        self.explode = explode
        self.source_container = ContainerFactory.container_from_ffprobe(self.infile,
                                                                        self.config.ffmpeg
                                                                        )
        self.target_container = Container(target, outputfile)

        self.output = outputfile
        self.options = []

        self.ob = OptionBuilder(self.source_container, self.target_container)

    def process(self):

        self.ob.generate_target_container(self.config.stream_formats,
                                          self.config.defaults,
                                          self.config.audio_languages,
                                          self.config.subtitle_languages,
                                          compare_presets=self.config.ignore)

        self.add_extra_audio_streams()
        self.ob.print_mapping(self.source_container, self.target_container, self.ob.mapping)
        self.config.ffmpeg.generate_commands(self.source_container, self.target_container, self.ob.mapping,
                                             self.config.encoder_factory)

    def add_extra_audio_streams(self):

        tpl = self.config.stream_formats

        extra_streams = []
        for cdc in [Codec(codec) for codec in self.config.audio_create_tracks]:
            stream = AudioStream(cdc)
            if cdc in tpl:
                stream.add_options(*tpl[cdc].options)
                extra_streams.append(stream)

        if extra_streams:
            for idx, stream in self.source_container.streams.items():
                if isinstance(stream, AudioStream):
                    if isinstance(stream, AudioStream):
                        b = False
                        for lng in self.config.audio_languages:
                            if lng == stream.options.get_unique_option(Language):
                                b = True
                                break

                        if not b:
                            continue

                    for t in extra_streams:
                        target_stream = AudioStream(t.codec)
                        target_stream.add_options(*t.options)
                        leftovers = list(filter(lambda x: not target_stream.options.has_option(x), stream.options))
                        target_stream.add_options(*leftovers)
                        self.ob.add_mapping(idx, target_stream, duplicate_check=True)

    def convert(self):
        try:
            for t in self.config.ffmpeg.convert(self.infile, self.output, self.options):
                log.debug(t)
            return self.output

        except:
            return None


if __name__ == '__main__':
    import os

    laptop = os.path.abspath('/Users/Jon/Downloads/in/The.Polar.Express.(2004).1080p.BluRay.MULTI.x264-DiG8ALL.mkv')
    desktop = os.path.abspath("/Users/Jon/Downloads/Geostorm 2017 1080p FR EN X264 AC3-mHDgz.mkv")
    cfgmgr = configuration.CfgMgr()
    cfgmgr.load('defaults.ini')
    p = Processor(cfgmgr.cfg, desktop, '/Users/jon/Downloads/toto.mp4', 'mp4')
    p.process()
#    p.convert()
