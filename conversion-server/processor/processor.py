import configuration
from converter_v2.optionbuilder import OptionBuilder
from converter_v2.containers import ContainerFactory
from converter_v2.streams import AudioStream
from converter_v2.streamoptions import *
import os
from converter_v2.encoders import EncoderFactory, Encoders
import logging
from converter_v2.ffmpeg import FFMpeg

# log = logging.getLogger()
# log.setLevel(logging.DEBUG)
# sh = logging.StreamHandler(sys.stdout)
# sh.setLevel(logging.DEBUG)
# formatter = logging.Formatter('%(levelname)s - %(message)s')
# sh.setFormatter(formatter)
# log.addHandler(sh)
log = logging.getLogger(__name__)

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

        #self.ffmpeg_path = self.config['FFMPEG']['ffmpeg']
        #elf.ffprobe_path = self.config['FFMPEG']['ffprobe']

        self.ffmpeg = FFMpeg(self.config['FFMPEG']['ffmpeg'], self.config['FFMPEG']['ffprobe'])
        self.ignore = {'video': self.config['Containers'][self.target]['video'].get('ignore_presets', False),
                       'audio': self.config['Containers'][self.target]['audio'].get('ignore_presets', False),
                       'subtitle': self.config['Containers'][self.target]['subtitle'].get('ignore_presets', False)}

        self.audio_create_tracks = self.config['Containers'][self.target]['audio']['force_create_tracks']

        self._stream_formats = self.load_stream_formats()
        self._encoders = self.load_encoders()
        self._defaults = self.load_defaults()


    @property
    def defaults(self):
        return self._defaults

    @property
    def encoders(self):
        return self._encoders

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
        _encoders = Encoders(self.ffmpeg)
        encs = []

        for _enc in self.config['EncoderOptions']:
            encoder = EncoderFactory.get_codec_by_name(_enc)
            if encoder:
                _options = Options()
                for k, v in self.config['EncoderOptions'][_enc].items():
                    _option = OptionFactory.get_option(k)
                    if _option:
                        _options.add_option(_option(v))

                if _options and _encoders.is_ffmpeg_encoder(encoder):
                    encoder.add_option(*_options.options)
                    encs.append(encoder)

        return encs


class Processor2(object):

    def __init__(self, config, inputfile, outputfile, target):
        """
        Creates a target container from the inputfile, taking into account the configuration
        :param config: a configuration object
        :type config: ConfigObj
        :param inputfile: path to the input file
        :type inputfile: os.path.abspath
        :param target: the target container to create
        :type target: str
        """
        self.config = ProcessorConfig(config, target)
        if os.path.exists(inputfile):
            self.infile = inputfile
        else:
            raise FileNotFoundError

        self.source_container = ContainerFactory.container_from_ffprobe(self.infile,
                                                                        self.config.ffmpeg
                                                                        )
        self.encoders = Encoders(self.config.ffmpeg)
        self.target = target
        self.output = outputfile
        self.output_file = None
        self.options = []

        self.ob = OptionBuilder(self.source_container, target)

    def process(self):

        self.ob.generate_mapping_2(self.config.stream_formats,
                                   self.config.defaults,
                                   self.config.audio_languages,
                                   self.config.subtitle_languages,
                                   compare_presets=self.config.ignore)

        self.add_extra_audio_streams_2()
        self.ob.prepare_encoders(self.encoders)

        self.options = self.ob.generate_options_2(*self.config.encoders)

    def add_extra_audio_streams_2(self):

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
                        target_stream.add_options(stream.options.get_unique_option(Language))
                        t_idx = self.ob.target_container.add_stream(target_stream, duplicate_check=True)
                        if t_idx:
                            self.ob.add_mapping_2(idx, t_idx)

    def convert(self):


        for t in self.config.ffmpeg.convert(self.infile, self.output, self.options):
            print(t)


class Processor(object):

    def __init__(self, config, inputfile, outputfile, target):
        """
        Creates a target container from the inputfile, taking into account the configuration
        :param config: a configuration object
        :type config: ConfigObj
        :param inputfile: path to the input file
        :type inputfile: os.path.abspath
        :param target: the target container to create
        :type target: str
        """
        self.config = config
        if os.path.exists(inputfile):
            self.infile = inputfile
        else:
            raise FileNotFoundError
        self.ffmpeg_path = self.config['FFMPEG']['ffmpeg']
        self.ffprobe_path = self.config['FFMPEG']['ffprobe']
        self.source_container = ContainerFactory.container_from_ffprobe(self.infile,
                                                                        self.ffmpeg_path,
                                                                        self.ffprobe_path
                                                                        )

        self.target = target
        self.output = outputfile
        self.output_file = None
        self.options = []
        self.stream_formats = self.load_stream_formats()
        self.defaults = self.load_defaults()
        self.encoders = self.load_encoders()
        self.ob = OptionBuilder(self.source_container, target)
        self.target_container = None

    def process(self):

        self.ob.generate_mapping_2(self.stream_formats, self.defaults,
                                   ignore_video=self.config['Containers'][self.target]['video']['ignore_presets'],
                                   ignore_audio=self.config['Containers'][self.target]['audio']['ignore_presets'],
                                   ignore_subtitle=self.config['Containers'][self.target]['subtitle']['ignore_presets'])
        self.add_extra_audio_streams_2()

        self.options = self.ob.generate_options_2(self.encoders)

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

        languages = []
        templates = {}

        for k in ['audio', 'video', 'subtitle']:
            if k == 'audio':
                languages = [Language(lng) for lng in self.config['Languages']['audio']]
            elif k == 'video':
                languages = []
            elif k == 'subtitle':
                languages = [Language(lng) for lng in self.config['Languages']['subtitle']]

            for _codec in self.config['Containers'][self.target][k]['accepted_track_formats']:

                _options = Options()

                if _codec in self.config['StreamFormats']:

                    for opt_name, opt_value in self.config['StreamFormats'][_codec].items():
                        option = OptionFactory.get_option(opt_name)
                        if option:
                            if isinstance(opt_value, list):
                                for v in opt_value:
                                    _options.add_option(option(v))
                            else:
                                _options.add_option(option(opt_value))

                for lng in languages:
                    _options.add_option(lng)
                templates.update({Codec(_codec): _options})

        return templates

    def load_encoders(self):
        _encoders = []

        for _enc in self.config['EncoderOptions']:
            encoder = EncoderFactory.get_codec_by_name(_enc)
            if encoder:
                _options = Options()
                for k, v in self.config['EncoderOptions'][_enc].items():
                    _option = OptionFactory.get_option(k)
                    if _option:
                        _options.add_option(_option(v))

                if _options:
                    encoder.add_option(*_options.options)
                    _encoders.append(encoder)

        return _encoders

    def add_extra_audio_streams(self):

        tpl = {}
        for _codec in self.config['Containers'][self.target]['audio']['accepted_track_formats']:

            _options = Options()

            if _codec in self.config['StreamFormats']:

                for opt_name, opt_value in self.config['StreamFormats'][_codec].items():
                    option = OptionFactory.get_option(opt_name)
                    if option:
                        if isinstance(opt_value, list):
                            for v in opt_value:
                                _options.add_option(option(v))
                        else:
                            _options.add_option(option(opt_value))
            tpl.update({Codec(_codec): _options})

        extra_streams = []
        for cdc in [Codec(codec) for codec in self.config['Containers'][self.target]['audio']['force_create_tracks']]:
            stream = AudioStream(cdc)
            if cdc in tpl:
                stream.add_options(*tpl[cdc].options)
                extra_streams.append(stream)

        if extra_streams:
            for idx, stream in self.source_container.streams.items():
                if isinstance(stream, AudioStream):
                    for target_stream in extra_streams:
                        target_stream.add_options(stream.options.get_unique_option(Language))
                        self.ob.add_mapping(idx, target_stream, duplicate_check=True)

    def add_extra_audio_streams_2(self):

        tpl = {}
        for _codec in self.config['Containers'][self.target]['audio']['accepted_track_formats']:

            _options = Options()

            if _codec in self.config['StreamFormats']:

                for opt_name, opt_value in self.config['StreamFormats'][_codec].items():
                    option = OptionFactory.get_option(opt_name)
                    if option:
                        if isinstance(opt_value, list):
                            for v in opt_value:
                                _options.add_option(option(v))
                        else:
                            _options.add_option(option(opt_value))
            tpl.update({Codec(_codec): _options})

        extra_streams = []
        for cdc in [Codec(codec) for codec in self.config['Containers'][self.target]['audio']['force_create_tracks']]:
            stream = AudioStream(cdc)
            if cdc in tpl:
                stream.add_options(*tpl[cdc].options)
                extra_streams.append(stream)

        if extra_streams:
            for idx, stream in self.source_container.streams.items():
                if isinstance(stream, AudioStream):
                    for target_stream in extra_streams:
                        target_stream.add_options(stream.options.get_unique_option(Language))
                        t_idx = self.ob.target_container.add_stream(target_stream, duplicate_check=True)
                        if t_idx:
                            self.ob.add_mapping_2(idx, t_idx)

    def convert(self):
        from converter_v2.ffmpeg import FFMpeg
        converter = FFMpeg(self.ffmpeg_path, self.ffprobe_path)
        for t in converter.convert(self.infile, self.output, self.options):
            print(t)


if __name__ == '__main__':
    import os

    laptop = os.path.abspath('/Users/Jon/Downloads/in/The.Polar.Express.(2004).1080p.BluRay.MULTI.x264-DiG8ALL.mkv')
    desktop = os.path.abspath("/Users/jon/Downloads/Geostorm 2017 1080p FR EN X264 AC3-mHDgz.mkv")
    cfgmgr = configuration.cfgmgr()
    cfgmgr.load('defaults.ini')
    p = Processor2(cfgmgr.cfg, desktop, '/Users/jon/Downloads/toto.mp4', 'mp4')
    p.process()
    p.convert()
