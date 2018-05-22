# coding=utf-8
import abc
from converter.avcodecs import CodecFactory
from converter.streaminfo import MediaInfo, MediaStreamInfo
import logging
import languagecode
import sys
import os
from  converter.streamformats import StreamFormatFactory
from typing import Union, Dict

log = logging.getLogger(__name__)


class OptionGenerator(object):
    supported_codecs = {'video': [],
                        'audio': [],
                        'subtitle': []}
    extension = ''  # type: str
    ffmpeg_format = ''  # type: str
    badcodecs = []  # type: list
    name = 'mp4'
    defaults = {
        'video': {
                  'prefer_method': 'option(copy, transcode, override, default=copy)',
                  'accepted_streams': 'force_list(default=list(h264, h265, hevc))',
                  'transcode_to': 'string(default=h264)',
                  'pix_fmts': 'force_list(default=None)',
                  'profiles': 'force_list(default=None)'
                },

        'audio': {
                  'accepted_streams': 'force_list(default=list(aac, ac3))',
                  'transcode_to': 'string(default=aac)',
                  'force_create_streams': 'force_list(default=None)',
                  'audio_copy_original': 'boolean(default=False)',
                  'create_multiple_stereo_streams': 'boolean(default=False)'
                 },

        'subtitles': {
                   'subtitle_streams': 'force_list(default=list(mov_text))',
                     },

        'process_same': 'boolean(default=False)',
        'preopts': 'string(default=None)',
        'postopts': 'string(default=None)'
              }

    def __init__(self, cfg, target) -> None:

        target = 'mp4'
        self.video = {'prefer_method': cfg['Containers'][target]['video'].get('prefer_method'),
                      'accepted_streams': cfg['Containers'][target]['video'].get('accepted_streams'),
                      'transcode_to': cfg['Containers'][target]['video'].get('transcode_to'),
                      'pix_fmts': cfg['Containers'][target]['video'].get('pix_fmts'),
                      'profiles': cfg['Containers'][target]['video'].get('profiles')
                      }

        self.audio = {'accepted_streams': cfg['Containers'][target]['audio'].get('accepted_streams'),
                      'transcode_to': cfg['Containers'][target]['audio'].get('transode_to'),
                      'force_create_streams': cfg['Containers'][target]['audio'].get('force_create_streams'),
                      'create_multiple_stereo_streams': cfg['Containers'][target]['audio'].get('create_multiple_stereo_streams'),
                      'accepted_languages': cfg['Languages'].get('audio')
                      }

#        self.subtitle = {'accepted_streams': cfg['Containers'][target]['subtitle'].get('accepted_streams'),
#                         'accepted_languages': cfg['Languages'].get('subtitle')
#                         }
        self.config = cfg
        self.preopts = cfg['Containers'][target].get('preopts') if cfg['Containers'][target].get('preopts') else []

        self.postopts = cfg['Containers'][target].get('postopts') if cfg['Containers'][target].get('postopts') else []


        self._streams = MediaInfo()


    def parse_video_options(self, source, stream=0):
        vencoder = None
        if source.video.codec in self.video['accepted_streams'] and self.video['prefer_method'] == 'copy':
            vencoder = CodecFactory.getvideo('copy', {})

        elif self.video['prefer_method'] == 'transcode':
            streamfmt = self.video['transcode_to']
            vencoder = StreamFormatFactory.get(streamfmt).getEncoder(self.config['StreamFormats'][streamfmt], self.config['StreamFormats'][streamfmt].get('encoder'))

        return vencoder

class ContainerFactory(object):

    containers = {}
    @classmethod
    def register(cls, ctn):
        cls.containers.update({ctn.name: ctn})

    @staticmethod
    def get(ctn: str, cfg: Dict):
        if ctn in ContainerFactory.containers:
            return ContainerFactory.containers[ctn](cfg)


class UnsupportedContainer(Exception):
    pass

if __name__ == '__main__':
    import configuration
    cfgmgr = configuration.cfgmgr()
    cfgmgr.load('defaults.ini')
    cfg = cfgmgr.cfg
    op = OptionGenerator(cfg, 'mp4')
    import converter.ffmpeg2
    ff = converter.FFMpeg('/usr/local/bin/ffmpeg', '/usr/local/bin/ffprobe')
    mediainfo = ff.probe('/Users/jon/Downloads/Geostorm 2017 1080p FR EN X264 AC3-mHDgz.mp4')
    toto = op.parse_video_options(source=mediainfo, stream=0)
    print('yeah')