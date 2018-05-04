# coding=utf-8
import abc
from collections import OrderedDict
from typing import List

import settings
from converter.avcodecs import *
from converter.ffmpeg import MediaInfo, MediaStreamInfo


class GenericContainer(object):
    __metaclass__ = abc.ABCMeta

    supported_codecs = {'video': [],
                        'audio': [],
                        'subtitle': []}
    extensions = []  # type: list[str]
    format = ''  # type: str
    badcodecs = []  # type: list
    configspecs = []

    def __init__(self) -> None:
        # Initialize copy codec
        pass

    @abc.abstractmethod
    def selecttracks(self, mediainfo: MediaInfo) -> List[MediaInfo]:
        pass

    @abc.abstractmethod
    def parse_options(self):
        pass

    @abc.abstractmethod
    def addstream(self, stream: MediaStreamInfo) -> bool:
        pass

    # TODO: Move to settings
    def getcodecs(self, typ: str):  # TODO : try/except block
        codeclist = OrderedDict()
        for codec_name in self.settings['Containers'][self.__class__.__name__.lower()][f'{typ.lower()}_codecs']:
            if codec_dict[typ.lower()][codec_name] in self.__class__.supported_codecs[typ.lower()]:
                codec = codec_dict[typ.lower()][codec_name]()
                codec.add_options(self.settings['Codecs'][typ][codec_name])
                codeclist[codec_name] = codec

        return codeclist


class MP4(GenericContainer):
    extensions = ['mp4', 'm4v']
    supported_codecs = {'video': [VideoCopyCodec, H264Codec, H265Codec, NVEncH264, H265Codec, NVEncH265],
                        'audio': [AacCodec, FdkAacCodec, Ac3Codec],
                        'subtitle': [SubtitleCopyCodec, MOVTextCodec]}
    supported_subtitle_codecs = [SubtitleCopyCodec, MOVTextCodec]
    badcodecs = ['truehd']
    format = 'mp4'
    name = 'mp4'

    configspecs = {
        'prefer_copy': 'boolean(default=True',
        'relocate_moov': 'boolean(default=True)',
        'ios_audio': 'boolean(default=True)',
        'ios_first_track_only': 'boolean(default=False)',
        'ios_move_last': 'boolean(default=False)',
        'ios_audio_filter': 'string(default=None)',
        'max_audio_channels': 'integer(1,6)',
        'audio_codecs': 'string_list(default=list(aac, ac3))',
        'video_codecs': 'string_list(default=list(h264, x264, h265))',
        'audio_copy_original': 'boolean(default=False)',
        'aac_adtstoasc': 'boolean(default=False)',
        'convert_mp4': 'boolean(default=False)',
        'embed_subs': 'boolean(default=True)',
        'embed_only_internal_subs': 'boolean(default=False)',
        'post_process': 'boolean(default=False)',
        'preopts': 'string(default=None)',
        'postopts': 'string(default=None)'
    }

    def __init__(self, mediainfo):
        """Handles initial loading of settings from settings manager as well as settings validation
        comparing them to both what's allowed in the container and the codec supported by the program"""
        self.mediainfo = mediainfo
        self.settings = settings.SettingsManager.getsettings('defaults')
        self.video_codecs = self.getcodecs('Video')
        self.audio_codecs = self.getcodecs('Audio')
        self.subtitle_codecs = self.getcodecs('Subtitle')

        super(MP4, self).__init__()

    def processstreams(self):
        if self.mediainfo.video:
            self.processvideo(self.mediainfo.video)

        if self.mediainfo.audio:
            self.processaudio(self.mediainfo.audio)

        if self.mediainfo.subtitle:
            self.processsubtitle(self.mediainfo.subtitle)

    def processvideo(self, streams):
        pass

    def processaudio(self, streams):
        pass

    def processsubtitle(self, streams):
        pass

    def addstream(self, stream: MediaStreamInfo) -> bool:
        """
        Adds the template for a stream to a container
        """

    def parse_options(self):
        pass


class MKV(GenericContainer):
    extensions = ['mkv']
    videocodecs = ['*']
    audiocodecs = ['*']
    subtitlecodecs = ['*']
    badcodecs = ['truehd']
    format = 'mkv'
    name = 'mkv'
    configspecs = {'coucou': 'integer(0,20,default=5)'}


Containers = []

for cls in GenericContainer.__subclasses__():
    Containers.append(cls)

if __name__ == '__main__':
    import converter
    conv = converter.Converter('/usr/local/bin/ffmpeg', '/usr/local/bin/ffprobe')
    mkvinfo = conv.probe('/Users/Jon/Downloads/in/mini.mkv')
    mp4 = MP4(mkvinfo)
    config = settings.SettingsManager.getsettings('defaults')
    initcodecs = {}
    toto = config['Codecs']['Video']

    for section in config['Codecs']['Video']:
        codec = video_codec_dict[section]()
        codec.add_options(config['Codecs']['Video'][section])
        initcodecs[section] = codec

    print('meuh')
