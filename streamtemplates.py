# coding=utf-8
from info.streaminfo import Container, SourceAudioStream, SourceVideoStream, SourceSubtitleStream, TargetAudioStream, \
    TargetVideoStream, TargetSubtitleStream
from typing import Type
import logging

log = logging.getLogger(__name__)


def filterlanguages(streamlist, languagelist, relax=False):
    validstreams = []
    for stream in streamlist:
        if stream.language in languagelist:
            validstreams.append(stream)

    if not validstreams and relax is True:
        return streamlist
    else:
        return validstreams


class StreamTemplate(object):
    def __init__(self, cfg, codecs):
        self.cfg = cfg
        self.codecs = codecs


class VideoStreamTemplate(StreamTemplate):
    def __init__(self, cfg, codecs: list):
        super(VideoStreamTemplate, self).__init__(cfg=cfg, codecs=codecs)

    def getStreamInfo(self, stream: Type[VideoStreamInfo], index) -> TargetVideoStream:
        assert isinstance(stream, VideoStreamInfo)

        if stream.codec in self.cfg:
            fmt = self.cfg[stream.codec]
            willtranscode = False
            if not fmt.get('pix_fmts') or stream.pix_fmt in fmt.get('pix_fmts'):
                pix_fmt = stream.pix_fmt
            else:
                pix_fmt = fmt['pix_fmts'][0]
                willtranscode = True

            if not fmt.get('max_height') or fmt['max_height'] > stream.height:
                height = stream.height
            else:
                height = fmt['max_height']
                willtranscode = True

            if not fmt.get('max_width') or fmt['max_width'] > stream.width:
                width = stream.width
            else:
                width = fmt['max_width']
                willtranscode = True

            if fmt.get('max_bitrate') and stream.bitrate and stream.bitrate > (fmt['max_bitrate'] * 1000):
                bitrate = fmt['max_bitrate']
                willtranscode = True
            else:
                bitrate = stream.bitrate

            if fmt.get('max_level') and stream.level and stream.level > fmt['max_level']:
                level = fmt['max_level']
                willtranscode = True
            else:
                level = stream.level

            # TODO : check that profile works
            if fmt.get('profile') and stream.profile and stream.profile == fmt['profile']:
                profile = fmt['profile']
                willtranscode = True
            else:
                profile = stream.profile

            return TargetVideoStream(index=index,
                                     codec=stream.codec,
                                     pix_fmt=pix_fmt,
                                     height=height,
                                     width=width,
                                     bitrate=bitrate,
                                     level=level,
                                     profile=profile,
                                     sourceindex=stream.index,
                                     willtranscode=willtranscode)

        else:
            raise Exception('Format not found')


class AudioStreamTemplate(StreamTemplate):

    def __init__(self, cfg, codecs):
        super(AudioStreamTemplate, self).__init__(cfg=cfg, codecs=codecs)

    def getStreamInfo(self, stream: Type[AudioStreamInfo], index) -> TargetAudioStream:
        assert isinstance(stream, AudioStreamInfo)

        if stream.codec in self.cfg:
            fmt = self.cfg[stream.codec]
            willtranscode = False

            if not fmt.get('max_bitrate') and stream.bitrate and stream.bitrate > fmt['max_bitrate']:
                bitrate = fmt['max_bitrate']
                willtranscode = True
            else:
                bitrate = stream.bitrate

            if not fmt.get('channels') or stream.channels > fmt['channels']:
                channels = stream.channels
            else:
                channels = fmt['channels']
                willtranscode = True

            language = stream.language

            return TargetAudioStream(index=index,
                                     codec=stream.codec,
                                     bitrate=bitrate,
                                     channels=channels,
                                     language=language,
                                     sourceindex=stream.index,
                                     willtranscode=willtranscode)


class SubtitleStreamTemplate(StreamTemplate):

    def __init__(self, cfg, codecs):
        super(SubtitleStreamTemplate, self).__init__(cfg=cfg, codecs=codecs)

    def getStreamInfo(self, stream: Type[SubtitleStreamInfo], index):
        # TODO
        willtranscode = False

        if stream.codec not in self.codecs:
            codec = self.codecs[0]
            willtranscode = True
        else:
            codec = stream.codec

        return TargetSubtitleStream(index=index,
                                    codec=codec,
                                    language=stream.language,
                                    sourceindex=stream.index,
                                    willtranscode=willtranscode)


class MissingFormatError(Exception):
    pass
