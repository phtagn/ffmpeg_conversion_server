import configuration
from converter_v2.streams import VideoStream, AudioStream, SubtitleStream, OptionBuilder
from converter_v2.containers import ContainerFactory
from converter_v2.templates import StreamTemplateFactory, Templates
from converter_v2.streamoptions import *
import converter_v2.ffmpeg

import os
import logging
import sys
#logging.basicConfig(filename='server.log', filemode='w', level=logging.DEBUG)
log = logging.getLogger()
log.setLevel(logging.DEBUG)
sh = logging.StreamHandler(sys.stdout)
sh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)s - %(message)s')
sh.setFormatter(formatter)
log.addHandler(sh)
"""Processes a video file in steps:
1) Analyse video file
2) Assess appropriate streams from options
3) Build templates from options
4) Build option list
5) Convert !
"""


class Processor(object):

    def __init__(self, config, inputfile, target):
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

    def _build_templates(self):

        templates = Templates()
        for k in ['audio', 'video', 'subtitle']:
            if k == 'audio':
                stream = AudioStream()
            elif k == 'video':
                stream = VideoStream()
            elif k == 'subtitle':
                stream = SubtitleStream()

            for codec in self.config['Containers'][self.target][k]['accepted_track_formats']:
                template = StreamTemplateFactory.get_stream_template(stream, Codec(codec))
                if codec in self.config['StreamFormats']:

                    for opt_name, opt_value in self.config['StreamFormats'][codec].items():
                        if isinstance(opt_value, list):
                            for v in opt_value:
                                template.add_option(OptionFactory.get_option(opt_name)(v))
                        else:
                            template.add_option(OptionFactory.get_option(opt_name)(opt_value))

                templates.add_template(template)

        return templates

    def process_languages(self):
        haslang = False

        l = []
        # This is necessary when the audio stream is not properly tagged. If we just match, there may be no audio in the
        # end, which is probably not what the user wants.
        for language in self.config['Languages']['audio']:
            l.append(AudioStream(Language(language)))
            for idx, stream in self.source_container.audio_streams.items():
                if stream.get_option_by_type(Language):
                    if stream.get_option_by_type(Language).value == language:
                        haslang = True
                        break

        if haslang:
            self.source_container.keep_matching_streams(*l)

        l = []
        for language in self.config['Languages']['subtitle']:
            l.append(SubtitleStream(Language(language)))
        self.source_container.keep_matching_streams(*l)

    def process_container(self):
        # First, remove languages that we do not want from audio and video
        self.process_languages()

        templates = self._build_templates()
        linked_container = ContainerFactory.container_from_templates(self.source_container, self.target, templates)

        # Second, add the audio tracks that we need, without duplication
        #for force_track in self.config['Containers'][self.target]['audio']['force_create_tracks']:
        #    for idx, audio_stream in self.source_container.audio_streams.items():
        #        aud = AudioStream(Codec(force_track), audio_stream.get_option_by_type(Language))
        #        linked_container.add_no_dup(((idx, audio_stream), aud))

        if logging.getLogger().getEffectiveLevel() == logging.DEBUG:
            log.debug('Analysis result:\n %s ', str(linked_container))

        return linked_container

    def convert(self, outputfile):
        ffmpeg = converter_v2.ffmpeg.FFMpeg(self.ffmpeg_path, self.ffprobe_path)
        ob = OptionBuilder()
        options = ob.build_options(tctn, {'aac': 'fdkaac'})
        if options:
            for timecode in ffmpeg.convert(self.infile, outputfile, options):
                print(timecode)
        else:
            raise Exception('No option were generated, cannot convert')


if __name__ == '__main__':
    laptop = '/Users/Jon/Downloads/in/The.Polar.Express.(2004).1080p.BluRay.MULTI.x264-DiG8ALL.mkv'
    desktop = "/Users/jon/Downloads/Geostorm 2017 1080p FR EN X264 AC3-mHDgz.mkv"
    cfgmgr = configuration.cfgmgr()
    cfgmgr.load('defaults.ini')
    p = Processor(cfgmgr.cfg, desktop, 'mp4')
    tctn = p.process_container()

#    for idx in range(len(tctn.stream_pairs)):
#        print(f'{idx}:')
#        t = tctn.print_compare(idx)
#        print('\n'.join(t))
#        print('\n')

#    p.convert('/Users/Jon/Downloads/test.mp4')
