from converter import avcodecs
from typing import Dict

class BaseStreamFormat(object):
    encoders = {}
    default_encoder = ''
    name = ''

    @classmethod
    def getEncoder(cls, encoder: str = None):
        """
        Returns an encoder from avcodecs. The encoder is instantiated with encoderoptions.
        If encoderoptions are invalid, they are disregaarded by the encoder.
        If encoder is not specified, returns the default encoder instantiated with encoderoptions.
        :param encoderoptions: Dict of options to pass the encoder
        :param encoder: str, name of the encoder
        :return: avcodecs.codec
        """
        if not encoder:
            return cls.encoders[cls.default_encoder]
        elif encoder in cls.encoders:
            return cls.encoders[encoder]


class VideoStreamFormat(BaseStreamFormat):
    format_options = {
        'bitrate': 'integer(default=1500)',
        'filter': 'string(default=None)',
        'pix_fmt': 'string(default=None)',
#        'width': 'integer(default=1280)',
#        'height': 'integer(default=720)',
        'mode': 'string(default=None)'
    }


class AudioStreamFormat(BaseStreamFormat):
    format_options = {
        'channels': 'integer(default=2)',
        'bitrate': 'integer(default=200)',
        'filter': 'string(default=None)'
    }


class SubtitleStreamFormat(BaseStreamFormat):
    format_options = {'encoding': 'string(default=UTF-8)'}


class TheoraStreamFormat(VideoStreamFormat):
    encoders = {'copy': avcodecs.VideoCopyCodec,
                'theora': avcodecs.TheoraCodec}

    default_encoder = 'theora'
    name = 'theora'
    format_options = VideoStreamFormat.format_options.copy()
    format_options.update({'quality': 'integer(default=5)'})


class DivxStreamFormat(VideoStreamFormat):
    encoders = {'copy': avcodecs.VideoCopyCodec,
                'divx': avcodecs.DivxCodec}
    default_encoder = 'divx'
    name = 'divx'



class Vp8StreamFormat(VideoStreamFormat):
    encoders = {'copy': avcodecs.VideoCopyCodec,
                'vp8': avcodecs.Vp8Codec}
    default_encoder = 'vp8'
    name = 'vp8'


class H263StreamFormat(VideoStreamFormat):
    encoders = {'copy': avcodecs.VideoCopyCodec,
                'h263': avcodecs.H263Codec}
    default_encoder = 'h263'
    name = 'h263'


class FlvStreamFormat(VideoStreamFormat):
    encoders = {'copy': avcodecs.VideoCopyCodec,
                'flv': avcodecs.FlvCodec}
    default_encoder = 'flv'
    name = 'flv'


class Mpeg1StreamFormat(VideoStreamFormat):
    encoders = {'copy': avcodecs.VideoCopyCodec,
                'mpeg1': avcodecs.Mpeg1Codec}
    default_encoder = 'mpeg1'
    name = 'mpeg1'


class Mpeg2StreamFormat(VideoStreamFormat):
    encoders = {'copy': avcodecs.VideoCopyCodec,
                'mpeg2': avcodecs.Mpeg2Codec}
    default_encoder = 'mpeg2'
    name = 'mpeg2'


class H264StreamFormat(VideoStreamFormat):
    encoders = {'copy': avcodecs.VideoCopyCodec,
                'h264': avcodecs.H264Codec,
                'h264sqv': avcodecs.H264QSV,
                'h264vaapi': avcodecs.H264VAAPI,
                'h264nvenc': avcodecs.NVEncH264
                }

    default_encoder = 'h264'
    name = 'h264'

    format_options = {
        'encoder': 'option(h264, h264qsv, h264vaapi, h264nvenc, default=h264)',
        'preset': 'string(default=None)',
        'crf': 'integer(default=23)',
        'profile': 'string(default=None)',
        'level': 'float(default=3.0)',
        'tune': 'string(default=None)'
    }

    format_options.update(VideoStreamFormat.format_options.copy())


class H265StreamFormat(VideoStreamFormat):
    encoders = {'copy': avcodecs.VideoCopyCodec,
                'h265': avcodecs.H265Codec,
                'hevcsqv': avcodecs.HEVCQSV,
                'h265nvenc': avcodecs.NVEncH265
                }

    default_encoder = 'h265'
    name = 'h265'
    format_options = {
        'encoder': 'option(h265, hevcqsv, h265nvenc, default=h265)',
        'preset': 'string(default=None)',
        'crf': 'integer(default=23)',
        'profile': 'string(default=None)',
        'level': 'float(default=3.0)',
        'tune': 'string(default=None)'
    }

    format_options.update(VideoStreamFormat.format_options.copy())


class VorbisStreamFormat(AudioStreamFormat):
    encoders = {'copy': avcodecs.AudioCopyCodec,
                'vorbis': avcodecs.VorbisCodec}
    default_encoder = 'vorbis'
    name = 'vorbis'
    format_options = AudioStreamFormat.format_options
    format_options.update({'quality': 'integer(default=3)'})


class Mp3StreamFormat(AudioStreamFormat):
    encoders = {'copy': avcodecs.AudioCopyCodec,
                'mp3': avcodecs.Mp3Codec}
    default_encoder = 'mp3'
    name = 'mp3'


class Mp2StreamFormat(AudioStreamFormat):
    encoders = {'copy': avcodecs.AudioCopyCodec,
                'mp2': avcodecs.Mp2Codec}
    default_encoder = 'mp2'
    name = 'mp2'


class Eac3StreamFormat(AudioStreamFormat):
    encoders = {'copy': avcodecs.AudioCopyCodec,
                'eac3': avcodecs.EAc3Codec}
    default_encoder = 'eac3'
    name = 'eac3'



class Ac3StreamFormat(AudioStreamFormat):
    encoders = {'copy': avcodecs.AudioCopyCodec,
                'ac3': avcodecs.Ac3Codec}
    default_encoder = 'ac3'
    name = 'ac3'


class DtsStreamFormat(AudioStreamFormat):
    encoders = {'copy': avcodecs.AudioCopyCodec,
                'dts': avcodecs.DtsCodec}
    default_encoder = 'dts'
    name = 'dts'


class FlacStreamFormat(AudioStreamFormat):
    encoders = {'copy': avcodecs.AudioCopyCodec,
                'flac': avcodecs.FlacCodec}
    default_encoder = 'flac'
    name = 'flac'


class AacStreamFormat(AudioStreamFormat):
    encoders = {'copy': avcodecs.AudioCopyCodec,
                'aac': avcodecs.AacCodec,
                'fdkaac': avcodecs.FdkAacCodec,
                'faac': avcodecs.FAacCodec}

    default_encoder = 'aac'
    name = 'aac'


class MovtextStreamFormat(SubtitleStreamFormat):
    encoders = {'copy': avcodecs.SubtitleCopyCodec,
                'moovtext': avcodecs.MOVTextCodec}
    default_encoder = 'moovtext'
    name = 'moovtext'


class SrtStreamFormat(SubtitleStreamFormat):
    encoders = {'copy': avcodecs.SubtitleCopyCodec,
                'srt': avcodecs.SrtCodec}
    default_encoder = 'srt'
    name = 'srt'


class SSAStreamFormat(SubtitleStreamFormat):
    encoders = {'copy': avcodecs.SubtitleCopyCodec,
                'ssa': avcodecs.SSA}
    default_encoder = 'ssa'
    name = 'ssa'


class SubRipStreamFormat(SubtitleStreamFormat):
    encoders = {'copy': avcodecs.SubtitleCopyCodec,
                'subrip': avcodecs.SubRip}
    default_encoder = 'subrip'
    name = 'subrip'



class DvdSubStreamFormat(SubtitleStreamFormat):
    encoders = {'copy': avcodecs.SubtitleCopyCodec,
                'dvdsub': avcodecs.DVDSub}
    default_encoder = 'dvdsub'
    name = 'dvdsub'


class DVBSubStreamFormat(SubtitleStreamFormat):
    encoders = {'copy': avcodecs.SubtitleCopyCodec,
                'dvbsub': avcodecs.DVBSub}
    default_encoder = 'dvbsub'
    name = 'dvbsub'


class WebVTTStreamFormat(SubtitleStreamFormat):
    encoders = {'copy': avcodecs.SubtitleCopyCodec,
                'webvtt': avcodecs.WebVTTCodec}
    default_encoder = 'webvtt'
    name = 'webvtt'


class StreamFormatFactory(object):

    formats = {
        'theora': TheoraStreamFormat,
        'h264': H264StreamFormat,
        'h265': H265StreamFormat,
        'divx': DivxStreamFormat,
        'vp8': Vp8StreamFormat,
        'h263': H263StreamFormat,
        'flv':  FlvStreamFormat,
        'mpeg1': Mpeg1StreamFormat,
        'mpeg2': Mpeg2StreamFormat,
        'vorbis': VorbisStreamFormat,
        'aac': AacStreamFormat,
        'mp3': Mp3StreamFormat,
        'mp2': Mp2StreamFormat,
        'eac3': Eac3StreamFormat,
        'dts': DtsStreamFormat,
        'flac': FlacStreamFormat,
        'movtext': MovtextStreamFormat,
        'srt': SrtStreamFormat,
        'ssa': SSAStreamFormat,
        'subrip': SubRipStreamFormat,
        'dvdsub': DvdSubStreamFormat,
        'dvbsub': DVBSubStreamFormat,
        'webvtt': WebVTTStreamFormat
    }

    @classmethod
    def get(cls, fmt):
        if fmt not in cls.formats:
            raise MissingFormatExcetption(f'Format {fmt} is unsupported. Available formats are {", ".join(cls.formats.keys())}')

        return cls.formats[fmt]

class MissingFormatExcetption(Exception):
    pass