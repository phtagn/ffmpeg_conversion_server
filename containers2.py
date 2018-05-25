# coding=utf-8
import abc
from converter.streaminfo import MediaInfo, MediaStreamInfo
import logging
import languagecode
import sys
import os
from converter.streamformats import StreamFormatFactory
from typing import Union, Dict
from streams import VideoStreamTemplate, AudioStreamTemplate, SubtitleStreamTemplate

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
            'accepted_track_formats': 'force_list(default=list(h264, h265, hevc))',
            'transcode_to': 'string(default=h264)'
        },

        'audio': {
            'accepted_track_formats': 'force_list(default=list(aac, ac3))',
            'transcode_to': 'string(default=aac)',
            'force_create_tracks': 'force_list(default=None)',
            'audio_copy_original': 'boolean(default=False)',
            'create_multiple_stereo_tracks': 'boolean(default=False)',
        },

        'subtitle': {
            'accepted_track_formats': 'force_list(default=list(mov_text))',
        },

        'process_same': 'boolean(default=False)',
        'preopts': 'string(default=None)',
        'postopts': 'string(default=None)'
    }

    def __init__(self, cfg, target) -> None:

        self.config = cfg

        target = 'mp4'
        self.video = {'prefer_method': cfg['Containers'][target]['video'].get('prefer_method'),
                      'transcode_to': cfg['Containers'][target]['video'].get('transcode_to')}

        self.audio = {'transcode_to': cfg['Containers'][target]['audio'].get('transcode_to'),
                      'force_create_tracks': cfg['Containers'][target]['audio'].get('force_create_tracks'),
                      'create_multiple_stereo_tracks': cfg['Containers'][target]['audio'].get(
                      'create_multiple_stereo_tracks'),
                      'accepted_languages': cfg['Languages'].get('audio')
                      }

        self.subtitle = {'accepted_languages': cfg['Languages'].get('subtitle')}

        self.preopts = cfg['Containers'][target].get('preopts') if cfg['Containers'][target].get('preopts') else []

        self.postopts = cfg['Containers'][target].get('postopts') if cfg['Containers'][target].get('postopts') else []

        self.videotemplates = {}

        for fmt in cfg['Containers'][target]['video'].get('accepted_track_formats'):
            if fmt not in cfg['TrackFormats']:
                raise MissingFormatError(
                    f'Formats {fmt} is unsupported. Supported formats are {cfg["TrackFormats"].keys()}')
            fmtopts = cfg['TrackFormats'][fmt]
            self.videotemplates.update({fmt: VideoStreamTemplate(codec=fmt,
                                                                 pix_fmts=fmtopts.get('pix_fmts'),
                                                                 profiles=fmtopts.get('profiles'),
                                                                 height=fmtopts.get('max_height'),
                                                                 width=fmtopts.get('max_width'),
                                                                 bitrate=fmtopts.get('bitrate'),
                                                                 sfilter=fmtopts.get('filter'),
                                                                 level=fmtopts.get('max_level'))})

        self.audiotemplates = {}

        for fmt in cfg['Containers'][target]['audio'].get('accepted_track_formats'):
            if fmt not in cfg['TrackFormats']:
                raise MissingFormatError(
                    f'Formats {fmt} is unsupported. Supported formats are {cfg["TrackFormats"].keys()}')
            fmtopts = cfg['TrackFormats'][fmt]
            self.audiotemplates.update({fmt: AudioStreamTemplate(codec=fmt,
                                                                 channels=fmtopts.get('max_channels'),
                                                                 bitrate=fmtopts.get('bitrate'),
                                                                 sfilter=fmtopts.get('filter'))})

        self.subtitletemplates = {}

        for fmt in cfg['Containers'][target]['subtitle'].get('accepted_track_formats'):
            if fmt not in cfg['TrackFormats']:
                raise MissingFormatError(
                    f'Formats {fmt} is unsupported. Supported formats are {cfg["TrackFormats"].keys()}')
            fmtopts = cfg['TrackFormats'][fmt]
            self.audiotemplates.update({fmt: AudioStreamTemplate(codec=fmt,
                                                                 channels=fmtopts.get('max_channels'),
                                                                 bitrate=fmtopts.get('bitrate'),
                                                                 sfilter=fmtopts.get('filter'))})

    def parse_video_options(self, source, stream=0):
        vencoder = None
        streamfmt = self.video['transcode_to']

        for videostream in source.videostreams:
            if self.video['prefer_method'] == 'copy':
                if videostream.codec in list(self.videotemplates.keys()):
                    encoder_name = 'copy'
                else:
                    encoder_name = self.config['TrackFormats'][streamfmt].get('encoder')

            if self.video['prefer_method'] == 'transcode':
                encoder_name = self.config['TrackFormats'][streamfmt].get('encoder')

            if self.video['prefer_method'] == 'override' and videostream.codec in list(self.videotemplates.keys()):
                if self.videotemplates[videostream.codec].conforms(videostream):
                    encoder_name = 'copy'
                else:
                    encoder_name = videostream.codec

            vencoder = StreamFormatFactory.get(videostream.codec).getEncoder(self.config['TrackFormats'][encoder_name].get('encoder'))

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


ContainerFactory.register(OptionGenerator)


class UnsupportedContainer(Exception):
    pass


class MissingFormatError(Exception):
    pass


if __name__ == '__main__':
    import configuration

    cfgmgr = configuration.cfgmgr()
    cfgmgr.load('defaults.ini')
    cfg = cfgmgr.cfg
    op = OptionGenerator(cfg, 'mp4')
    import converter.ffmpeg2

    ff = converter.ffmpeg2.FFMpeg('/usr/local/bin/ffmpeg', '/usr/local/bin/ffprobe')
    mediainfo = ff.probe('/Users/Jon/Downloads/in/The.Polar.Express.(2004).1080p.BluRay.MULTI.x264-DiG8ALL.mkv')
    toto = op.parse_video_options(source=mediainfo, stream=0)
    print('yeah')
