from typing import List
from converter_v2.encoders import *


class BaseStreamFormat(object):
    encoders = {}
    default_encoder = ''
    name = ''
    supported_options = []

    def __init__(self, options: List[IStreamOption] = list):
        self.options = []
        for opt in options:
            self.add_option(opt)

    def add_option(self, option: IStreamOption):

        assert isinstance(option, IStreamOption)

        if type(option) in self.supported_options:
            self.options.append(option)
        else:
            log.error('Option %s is not supported', option.name)

    @classmethod
    def getEncoder(cls, encoder: str = 'default'):
        """
        Returns an encoder from avcodecs. The encoder is instantiated with encoderoptions.
        If encoderoptions are invalid, they are disregaarded by the encoder.
        If encoder is not specified, returns the default encoder instantiated with encoderoptions.
        :param encoderoptions: Dict of options to pass the encoder
        :param encoder: str, name of the encoder
        :return: avcodecs.codec
        """
        if encoder == 'default':
            return cls.encoders[cls.default_encoder]
        elif encoder in cls.encoders:
            return cls.encoders[encoder]
        else:
            raise Exception(f'Encoder {encoder} not in {", ".join(cls.encoders)}')


class VideoStreamFormat(BaseStreamFormat):
    supported_options = [Codec, Bitrate]


class AudioStreamFormat(BaseStreamFormat):
    supported_options = [Codec, Bitrate, Channels, Language]


class SubtitleStreamFormat(BaseStreamFormat):
    supported_options = [Codec, Language]


class TheoraStreamFormat(VideoStreamFormat):
    encoders = {'copy': CopyEncoder,
                'theora': encoders.TheoraCodec}
    default_encoder = 'theora'
    name = 'theora'


class DivxStreamFormat(VideoStreamFormat):
    encoders = {'copy': encoders.VideoCopyEncoder,
                'divx': encoders.DivxCodec}
    default_encoder = 'divx'
    name = 'divx'


class Vp8StreamFormat(VideoStreamFormat):
    encoders = {'copy': encoders.VideoCopyEncoder,
                'vp8': encoders.Vp8Codec}
    default_encoder = 'vp8'
    name = 'vp8'


class H263StreamFormat(VideoStreamFormat):
    encoders = {'copy': encoders.VideoCopyEncoder,
                'h263': encoders.H263Codec}
    default_encoder = 'h263'
    name = 'h263'


class FlvStreamFormat(VideoStreamFormat):
    encoders = {'copy': encoders.VideoCopyEncoder,
                'flv': encoders.FlvCodec}
    default_encoder = 'flv'
    name = 'flv'


class Mpeg1StreamFormat(VideoStreamFormat):
    encoders = {'copy': encoders.VideoCopyEncoder,
                'mpeg1': encoders.Mpeg1Codec}
    default_encoder = 'mpeg1'
    name = 'mpeg1'


class Mpeg2StreamFormat(VideoStreamFormat):
    encoders = {'copy': encoders.VideoCopyEncoder,
                'mpeg2': encoders.Mpeg2Codec}
    default_encoder = 'mpeg2'
    name = 'mpeg2'


class H264StreamFormat(VideoStreamFormat):
    encoders = {'copy': encoders.VideoCopyEncoder,
                'h264': encoders.H264Codec,
                'h264qsv': encoders.H264QSV,
                'h264vaapi': encoders.H264VAAPI,
                'nvenc_h264': encoders.NVEncH264
                }

    default_encoder = 'h264'
    name = 'h264'

    format_options = {
        'encoder': 'option(h264, h264qsv, h264vaapi, nvenc_h264, default=h264)',
        'profiles': 'force_list(default=None)',
        'pix_fmts': 'force_list(default=None)',
        'max_level': 'float(default=3.0)'
    }

    format_options.update(VideoStreamFormat.format_options.copy())


class H265StreamFormat(VideoStreamFormat):
    encoders = {'copy': encoders.VideoCopyEncoder,
                'h265': encoders.H265Codec,
                'hevcsqv': encoders.HEVCQSV,
                'nvenc_h265': encoders.NVEncH265
                }

    default_encoder = 'h265'
    name = 'hevc'
    format_options = {
        'encoder': 'option(h265, hevcqsv, nvenc_h265, default=h265)',
        'preset': 'string(default=None)',
        'profiles': 'force_list(default=None)',
        'level': 'float(default=3.0)'
    }

    format_options.update(VideoStreamFormat.format_options.copy())


class VorbisStreamFormat(AudioStreamFormat):
    encoders = {'copy': encoders.AudioCopyEncoder,
                'vorbis': encoders.VorbisCodec}
    default_encoder = 'vorbis'
    name = 'vorbis'


class Mp3StreamFormat(AudioStreamFormat):
    encoders = {'copy': encoders.AudioCopyEncoder,
                'mp3': encoders.Mp3Codec}
    default_encoder = 'mp3'
    name = 'mp3'


class Mp2StreamFormat(AudioStreamFormat):
    encoders = {'copy': encoders.AudioCopyEncoder,
                'mp2': encoders.Mp2Codec}
    default_encoder = 'mp2'
    name = 'mp2'


class Eac3StreamFormat(AudioStreamFormat):
    encoders = {'copy': encoders.AudioCopyEncoder,
                'eac3': encoders.EAc3Codec}
    default_encoder = 'eac3'
    name = 'eac3'


class Ac3StreamFormat(AudioStreamFormat):
    encoders = {'copy': encoders.AudioCopyEncoder,
                'ac3': encoders.Ac3Codec}
    default_encoder = 'ac3'
    name = 'ac3'
    format_options = AudioStreamFormat.format_options.copy()
    format_options.update({'max_bitrate': 'integer(default=384)',
                           'max_channels': 'integer(default=6)'})


class DtsStreamFormat(AudioStreamFormat):
    encoders = {'copy': encoders.AudioCopyEncoder,
                'dts': encoders.DtsCodec}
    default_encoder = 'dts'
    name = 'dts'


class FlacStreamFormat(AudioStreamFormat):
    encoders = {'copy': encoders.AudioCopyEncoder,
                'flac': encoders.FlacCodec}
    default_encoder = 'flac'
    name = 'flac'


class AacStreamFormat(AudioStreamFormat):
    encoders = {'copy': encoders.AudioCopyEncoder,
                'aac': encoders.AacCodec,
                'fdkaac': encoders.FdkAacCodec,
                'faac': encoders.FAacCodec}

    default_encoder = 'aac'
    name = 'aac'


class MovtextStreamFormat(SubtitleStreamFormat):
    encoders = {'copy': encoders.SubtitleCopyEncoder,
                'mov_text': encoders.MOVTextCodec}
    default_encoder = 'mov_text'
    name = 'mov_text'


class SrtStreamFormat(SubtitleStreamFormat):
    encoders = {'copy': encoders.SubtitleCopyEncoder,
                'srt': encoders.SrtCodec}
    default_encoder = 'srt'
    name = 'srt'


class SSAStreamFormat(SubtitleStreamFormat):
    encoders = {'copy': encoders.SubtitleCopyEncoder,
                'ssa': encoders.SSA}
    default_encoder = 'ssa'
    name = 'ssa'


class SubRipStreamFormat(SubtitleStreamFormat):
    encoders = {'copy': encoders.SubtitleCopyEncoder,
                'subrip': encoders.SubRip}
    default_encoder = 'subrip'
    name = 'subrip'


class DvdSubStreamFormat(SubtitleStreamFormat):
    encoders = {'copy': encoders.SubtitleCopyEncoder,
                'dvdsub': encoders.DVDSub}
    default_encoder = 'dvdsub'
    name = 'dvdsub'


class DVBSubStreamFormat(SubtitleStreamFormat):
    encoders = {'copy': encoders.SubtitleCopyEncoder,
                'dvbsub': encoders.DVBSub}
    default_encoder = 'dvbsub'
    name = 'dvbsub'


class WebVTTStreamFormat(SubtitleStreamFormat):
    encoders = {'copy': encoders.SubtitleCopyEncoder,
                'webvtt': encoders.WebVTTCodec}
    default_encoder = 'webvtt'
    name = 'webvtt'


class StreamFormatFactory(object):
    formats = {
        'theora': TheoraStreamFormat,
        'h264': H264StreamFormat,
        'x264': H264StreamFormat,  # Alias
        'h265': H265StreamFormat,
        'hevc': H265StreamFormat,  # Alias
        'divx': DivxStreamFormat,
        'vp8': Vp8StreamFormat,
        'h263': H263StreamFormat,
        'flv': FlvStreamFormat,
        'mpeg1': Mpeg1StreamFormat,
        'mpeg2': Mpeg2StreamFormat,

        'vorbis': VorbisStreamFormat,
        'aac': AacStreamFormat,
        'mp3': Mp3StreamFormat,
        'mp2': Mp2StreamFormat,
        'ac3': Ac3StreamFormat,
        'eac3': Eac3StreamFormat,
        'dts': DtsStreamFormat,
        'flac': FlacStreamFormat,

        'mov_text': MovtextStreamFormat,
        'srt': SrtStreamFormat,
        'ssa': SSAStreamFormat,
        'subrip': SubRipStreamFormat,
        'dvdsub': DvdSubStreamFormat,
        'dvbsub': DVBSubStreamFormat,
        'webvtt': WebVTTStreamFormat
    }

    @classmethod
    def get_format(cls, fmt):
        if fmt not in cls.formats:
            raise MissingFormatExcetption(
                f'Format {fmt} is unsupported. Available formats are {", ".join(cls.formats.keys())}')

        return cls.formats[fmt]


class MissingFormatExcetption(Exception):
    pass
