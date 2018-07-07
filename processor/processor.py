import configuration
from converter_v2.streams import VideoStream, AudioStream, SubtitleStream, StreamFactory
from converter_v2.optionbuilder import OptionBuilder
from converter_v2.containers import ContainerFactory
from converter_v2.streamoptions import *
import converter_v2.ffmpeg

from converter_v2.encoders import CodecFactory
import os
import sys
import logging

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


class Processor(object):

    def __init__(self, config, inputfile, target):
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

    def get_defaults(self):
        defaults = {}
        for k in ['audio', 'video', 'subtitle']:
            _options = Options()
            try:
                _codec = self.config['Containers'][self.target][k]['accepted_track_formats'][0]
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

    def generate_stream_templates(self):

        languages = []
        templates = {}
        _codec = None

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

                if _options:
                    for lng in languages:
                        _options.add_option(lng)
                    templates.update({Codec(_codec): _options})

        return templates

    def generate_encoder_options(self):
        _encoders = {}
        _options = None
        _enc = None

        for _enc in self.config['Encoders']:
            _options = Options()
            for k, v in self.config['Encoders'][_enc].items():
                _option = OptionFactory.get_option(k)
                if _option:
                    _options.add_option(_option(v))

            if _options:
                _encoders.update({_enc.lower(): _options})

        return _encoders

    def process_container(self):

        ob = OptionBuilder(self.source_container, self.generate_stream_templates(), self.get_defaults(),
                           self.generate_encoder_options())
        ob.generate_mapping()
        ob.generate_options()
        print(True)
        return ob

    def convert(self, container, outputfile):
        pass


if __name__ == '__main__':
    import os

    laptop = os.path.abspath('/Users/Jon/Downloads/in/The.Polar.Express.(2004).1080p.BluRay.MULTI.x264-DiG8ALL.mkv')
    desktop = os.path.abspath("/Users/jon/Downloads/Geostorm 2017 1080p FR EN X264 AC3-mHDgz.mkv")
    cfgmgr = configuration.cfgmgr()
    cfgmgr.load('defaults.ini')
    p = Processor(cfgmgr.cfg, laptop, 'mp4')
    p.process_container()
