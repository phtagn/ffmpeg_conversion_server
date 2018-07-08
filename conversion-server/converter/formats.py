#!/usr/bin/env python
from converter.streamformats import StreamFormatFactory as sf
import logging
log = logging.getLogger(__name__)

# TODO: finish gruntwork and input all of the supported stream formats

class ContainerFormat(object):
    """
    Base format class.

    Supported formats are: ogg, avi, mkv, webm, flv, mov, mp4, mpeg
    """

    format_name = ''  # type: str
    ffmpeg_format_name = ''  # type: str
    audio_supported_codecs = []  # type: list
    video_supported_codecs = []  # type: list
    subtitle_supported_codecs = []  # type: list
    format_extension = ''  # type: str

    @classmethod
    def parse_options(cls):
        # if 'format' not in opt or opt.get('format') != self.format_name:
        #    raise ValueError('invalid Format format')
        return ['-f', cls.ffmpeg_format_name]

    @classmethod
    def supports(cls, codec: str, typ: str) -> bool:
        """
        Method to test if the container supports the codec.
        :param codec: str, the name of the codec
        :param typ: str, the type of the container (e.g. mp4, mkv)
        :return: True if container supports the codec, False if not
        """
        if typ == 'video':
            codecs = cls.video_supported_codecs
        elif typ == 'audio':
            codecs = cls.audio_supported_codecs
        elif typ == 'subtitle':
            codecs = cls.subtitle_supported_codecs
        else:
            raise Exception(f'{typ} not one of video, audio, subtitle')

        if codec in [cdc.name for cdc in codecs]:
            return True
        else:
            log.debug('Codec %s not supported by container %s, discarding stream', codec, cls.format_name)
            return False


class OggFormat(ContainerFormat):
    """
    Ogg container format, mostly used with Vorbis and Theora.
    """
    format_name = 'ogg'
    ffmpeg_format_name = 'ogg'
    format_extension = '.ogg'
    audio_supported_codecs = list(map(sf.get_format, ['vorbis', 'flac']))
    video_supported_codecs = list(map(sf.get_format, ['theora']))
    subtitle_supported_codecs = list(map(sf.get_format, ['subrip']))


class AviFormat(ContainerFormat):
    """
    Avi container format, often used vith DivX video.
    """
    format_name = 'avi'
    ffmpeg_format_name = 'avi'
    format_extension = '.avi'
    audio_supported_codecs = list(map(sf.get_format, ['mp3', 'aac', 'ac3', 'dts']))
    video_supported_codecs = list(map(sf.get_format, ['mpeg1', 'mpeg2', 'h264', 'divx']))


class MkvFormat(ContainerFormat):
    """
    Matroska format, often used with H.264 video.
    """
    format_name = 'mkv'
    ffmpeg_format_name = 'matroska'
    audio_supported_codecs = list(map(sf.get_format, ['vorbis', 'aac', 'mp3', 'mp2', 'ac3', 'eac3', 'dts', 'flac']))
    video_supported_codecs = list(
        map(sf.get_format, ['theora', 'h264', 'hevc', 'divx', 'vp8', 'h263', 'mpeg1', 'mpeg2']))
    subtitle_supported_codecs = list(
        map(sf.get_format, ['mov_text', 'srt', 'ssa', 'subrip', 'dvdsub', 'dvbsub', 'webvtt']))


class WebmFormat(ContainerFormat):
    """
    WebM is Google's variant of Matroska containing only
    VP8 for video and Vorbis for audio content.
    """
    format_name = 'webm'
    ffmpeg_format_name = 'webm'
    format_extension = '.webm'
    audio_supported_codecs = list(map(sf.get_format, ['vorbis']))
    video_supported_codecs = list(map(sf.get_format, ['vp8']))


class FlvFormat(ContainerFormat):
    """
    Flash Video container format.
    """
    format_name = 'flv'
    ffmpeg_format_name = 'flv'
    video_supported_codecs = [sf.get_format('h264')]
    audio_supported_codecs = [sf.get_format('mp3'), sf.get_format('aac')]


class MovFormat(ContainerFormat):
    """
    Mov container format, used mostly with H.264 video
    content, often for mobile platforms.
    """
    format_name = 'mov'
    ffmpeg_format_name = 'mov'
    format_extension = '.mov'
    video_supported_codecs = list(map(sf.get_format, ['mpeg1', 'mpeg2', 'h264', 'hevc', 'theora']))
    audio_supported_codecs = list(map(sf.get_format, ['mp3', 'vorbis', 'aac', 'flac']))
    subtitle_supported_codecs = list(map(sf.get_format, ['mov_text']))


class Mp4Format(ContainerFormat):
    """
    Mp4 container format, the default Format for H.264
    video content.
    """
    format_name = 'mp4'
    ffmpeg_format_name = 'mp4'
    video_supported_codecs = list(map(sf.get_format, ['mpeg1', 'mpeg2', 'h264', 'hevc', 'theora', 'vp8']))
    audio_supported_codecs = list(map(sf.get_format, ['mp3', 'aac', 'ac3', 'eac3', 'dts']))
    subtitle_supported_codecs = list(map(sf.get_format, ['mov_text']))


class MpegFormat(ContainerFormat):
    """
    MPEG(TS) container, used mainly for MPEG 1/2 video codecs.
    """
    format_name = 'mpg'
    ffmpeg_format_name = 'mpegts'


class Mp3Format(ContainerFormat):
    """
    Mp3 container, used audio-only mp3 files
    """
    format_name = 'mp3'
    ffmpeg_format_name = 'mp3'


class SrtFormat(ContainerFormat):
    """
    SRT subtitle format
    """
    format_name = 'srt'
    ffmpeg_format_name = 'srt'


class WebVTTFormat(ContainerFormat):
    """
    VTT subtitle format
    """
    format_name = 'webvtt'
    ffmpeg_format_name = 'webvtt'


class SsaFormat(ContainerFormat):
    """
    SSA subtitle format
    """
    format_name = 'ass'
    ffmpeg_format_name = 'ass'


format_list = [
    OggFormat, AviFormat, MkvFormat, WebmFormat, FlvFormat,
    MovFormat, Mp4Format, MpegFormat, Mp3Format, SrtFormat,
    WebVTTFormat, SsaFormat
]


class FormatFactory():
    @staticmethod
    def get_format(format):
        f = [fmt for fmt in format_list if fmt.format_name == format]

        if len(f) == 1:
            return f[0]
        else:
            raise Exception(f'Unsupported format. Supported formats are: {" ,".join(f)}')
