from converter import avcodecs
from typing import Dict

class BaseStreamFormat(object):
    encoders = {}
    default_encoder = ''
    name = ''

    def __init__(self, encoderoptions, encoder=None):
        if not encoder:
            self._encoder = self.encoders[self.default_encoder](encoderoptions)
        elif encoder in self.encoders:
            self._encoder = self.encoders[encoder](encoderoptions)

    @property
    def encoder(self):
        return self._encoder

    @classmethod
    def getEncoder(cls, encoderoptions: Dict, encoder: str = None):
        """
        Returns an encoder from avcodecs. The encoder is instantiated with encoderoptions.
        If encoderoptions are invalid, they are disregaarded by the encoder.
        If encoder is not specified, returns the default encoder instantiated with encoderoptions.
        :param encoderoptions: Dict of options to pass the encoder
        :param encoder: str, name of the encoder
        :return: avcodecs.codec
        """
        if not encoder:
            return cls.encoders[cls.default_encoder](encoderoptions)
        elif encoder in cls.encoders:
            return cls.encoders[encoder](encoderoptions)


class VideoStreamFormat(BaseStreamFormat):
    format_options = {
        'bitrate': 'integer(default=1500)',
        'filter': 'string(default=None)',
        'pix_fmt': 'string(default=None)',
        'width': 'integer(default=1280)',
        'height': 'integer(default=720)',
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
    encoders = {'theora': avcodecs.TheoraCodec}
    default_encoder = 'theora'
    name = 'theora'
    format_options = VideoStreamFormat.format_options.copy()
    format_options.update({'quality': 'integer(default=5)'})

    def __init__(self, encoderoptions, encoder=None):
        super(TheoraStreamFormat, self).__init__(encoderoptions=encoderoptions, encoder=encoder)


class DivxStreamFormat(VideoStreamFormat):
    encoders = {'divx': avcodecs.DivxCodec}
    default_encoder = 'divx'
    name = 'divx'

    def __init__(self, encoderoptions, encoder=None):
        super(DivxStreamFormat, self).__init__(encoderoptions=encoderoptions, encoder=encoder)


class Vp8StreamFormat(VideoStreamFormat):
    encoders = {'vp8': avcodecs.Vp8Codec}
    default_encoder = 'vp8'
    name = 'vp8'

    def __init__(self, encoderoptions, encoder=None):
        super(Vp8StreamFormat, self).__init__(encoderoptions=encoderoptions, encoder=encoder)


class H263StreamFormat(VideoStreamFormat):
    encoders = {'h263': avcodecs.H263Codec}
    default_encoder = 'h263'
    name = 'h263'

    def __init__(self, encoderoptions, encoder=None):
        super(H263StreamFormat, self).__init__(encoderoptions=encoderoptions, encoder=encoder)


class FlvStreamFormat(VideoStreamFormat):
    encoders = {'flv': avcodecs.FlvCodec}
    default_encoder = 'flv'
    name = 'flv'

    def __init__(self, encoderoptions, encoder=None):
        super(FlvStreamFormat, self).__init__(encoderoptions=encoderoptions, encoder=encoder)


class Mpeg1StreamFormat(VideoStreamFormat):
    encoders = {'mpeg1': avcodecs.Mpeg1Codec}
    default_encoder = 'mpeg1'
    name = 'mpeg1'

    def __init__(self, encoderoptions, encoder=None):
        super(Mpeg1StreamFormat, self).__init__(encoderoptions=encoderoptions, encoder=encoder)


class Mpeg2StreamFormat(VideoStreamFormat):
    encoders = {'mpeg2': avcodecs.Mpeg2Codec}
    default_encoder = 'mpeg2'
    name = 'mpeg2'

    def __init__(self, encoderoptions, encoder=None):
        super(Mpeg2StreamFormat, self).__init__(encoderoptions=encoderoptions, encoder=encoder)


class H264StreamFormat(VideoStreamFormat):
    encoders = {'h264': avcodecs.H264Codec,
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

    def __init__(self, encoderoptions, encoder=None):
        super(H264StreamFormat, self).__init__(encoderoptions=encoderoptions, encoder=encoder)


class H265StreamFormat(VideoStreamFormat):
    encoders = {'h265': avcodecs.H265Codec,
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


    def __init__(self, encoderoptions, encoder=None):
        super(H265StreamFormat, self).__init__(encoderoptions=encoderoptions, encoder=encoder)


class VorbisStreamFormat(AudioStreamFormat):
    encoders = {'vorbis': avcodecs.VorbisCodec}
    default_encoder = 'vorbis'
    name = 'vorbis'
    format_options = AudioStreamFormat.format_options
    format_options.update({'quality': 'integer(default=3)'})

    def __init__(self, encoderoptions, encoder=None):
        super(VorbisStreamFormat, self).__init__(encoderoptions=encoderoptions, encoder=encoder)


class Mp3StreamFormat(AudioStreamFormat):
    encoders = {'mp3': avcodecs.Mp3Codec}
    default_encoder = 'mp3'
    name = 'mp3'

    def __init__(self, encoderoptions, encoder=None):
        super(Mp3StreamFormat, self).__init__(encoderoptions=encoderoptions, encoder=encoder)


class Mp2StreamFormat(AudioStreamFormat):
    encoders = {'mp2': avcodecs.Mp2Codec}
    default_encoder = 'mp2'
    name = 'mp2'

    def __init__(self, encoderoptions, encoder=None):
        super(Mp2StreamFormat, self).__init__(encoderoptions=encoderoptions, encoder=encoder)


class Eac3StreamFormat(AudioStreamFormat):
    encoders = {'eac3': avcodecs.EAc3Codec}
    default_encoder = 'eac3'
    name = 'eac3'

    def __init__(self, encoderoptions, encoder=None):
        super(Eac3StreamFormat, self).__init__(encoderoptions=encoderoptions, encoder=encoder)


class Ac3StreamFormat(AudioStreamFormat):
    encoders = {'ac3': avcodecs.Ac3Codec}
    default_encoder = 'ac3'
    name = 'ac3'

    def __init__(self, encoderoptions, encoder=None):
        super(Ac3StreamFormat, self).__init__(encoderoptions=encoderoptions, encoder=encoder)


class DtsStreamFormat(AudioStreamFormat):
    encoders = {'dts': avcodecs.DtsCodec}
    default_encoder = 'dts'
    name = 'dts'

    def __init__(self, encoderoptions, encoder=None):
        super(DtsStreamFormat, self).__init__(encoderoptions=encoderoptions, encoder=encoder)


class FlacStreamFormat(AudioStreamFormat):
    encoders = {'flac': avcodecs.FlacCodec}
    default_encoder = 'flac'
    name = 'flac'

    def __init__(self, encoderoptions, encoder=None):
        super(FlacStreamFormat, self).__init__(encoderoptions=encoderoptions, encoder=encoder)


class AacStreamFormat(AudioStreamFormat):
    encoders = {'aac': avcodecs.AacCodec,
                'fdkaac': avcodecs.FdkAacCodec,
                'faac': avcodecs.FAacCodec}

    default_encoder = 'aac'
    name = 'aac'

    def __init__(self, encoderoptions, encoder=None):
        super(AacStreamFormat, self).__init__(encoderoptions=encoderoptions, encoder=encoder)


class MovtextStreamFormat(SubtitleStreamFormat):
    encoders = {'moovtext': avcodecs.MOVTextCodec}
    default_encoder = 'moovtext'
    name = 'moovtext'

    def __init__(self, encoderoptions, encoder=None):
        super(MovtextStreamFormat, self).__init__(encoderoptions=encoderoptions, encoder=encoder)


class SrtStreamFormat(SubtitleStreamFormat):
    encoders = {'srt': avcodecs.SrtCodec}
    default_encoder = 'srt'
    name = 'srt'

    def __init__(self, encoderoptions, encoder=None):
        super(SrtStreamFormat, self).__init__(encoderoptions=encoderoptions, encoder=encoder)


class SSAStreamFormat(SubtitleStreamFormat):
    encoders = {'ssa': avcodecs.SSA}
    default_encoder = 'ssa'
    name = 'ssa'

    def __init__(self, encoderoptions, encoder=None):
        super(SSAStreamFormat, self).__init__(encoderoptions=encoderoptions, encoder=encoder)


class SubRipStreamFormat(SubtitleStreamFormat):
    encoders = {'subrip': avcodecs.SubRip}
    default_encoder = 'subrip'
    name = 'subrip'

    def __init__(self, encoderoptions, encoder=None):
        super(SubRipStreamFormat, self).__init__(encoderoptions=encoderoptions, encoder=encoder)


class DvdSubStreamFormat(SubtitleStreamFormat):
    encoders = {'dvdsub': avcodecs.DVDSub}
    default_encoder = 'dvdsub'
    name = 'dvdsub'

    def __init__(self, encoderoptions, encoder=None):
        super(DvdSubStreamFormat, self).__init__(encoderoptions=encoderoptions, encoder=encoder)


class DVBSubStreamFormat(SubtitleStreamFormat):
    encoders = {'dvbsub': avcodecs.DVBSub}
    default_encoder = 'dvbsub'
    name = 'dvbsub'

    def __init__(self, encoderoptions, encoder=None):
        super(DVBSubStreamFormat, self).__init__(encoderoptions=encoderoptions, encoder=encoder)


class WebVTTStreamFormat(SubtitleStreamFormat):
    encoders = {'webvtt': avcodecs.WebVTTCodec}
    default_encoder = 'webvtt'
    name = 'webvtt'

    def __init__(self, encoderoptions, encoder=None):
        super(WebVTTStreamFormat, self).__init__(encoderoptions=encoderoptions, encoder=encoder)

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