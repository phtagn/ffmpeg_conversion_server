from converter_v2.encoders import *


class BaseStreamFormat(object):
    encoders = {}
    default_encoder = ''
    name = ''
    supported_options = []

    @classmethod
    def get_encoder(cls, encoder, *options):

        if encoder and encoder.lower() == 'default' or not encoder:
            return cls.encoders[cls.default_encoder](*options)
        elif encoder in cls.encoders:
            return cls.encoders[encoder](*options)
        else:
            raise Exception(f'Encoder {encoder} not in {", ".join(cls.encoders)}')


class VideoStreamFormat(BaseStreamFormat):
    supported_options = [Codec, Bitrate]


class AudioStreamFormat(BaseStreamFormat):
    supported_options = [Codec, Bitrate, Channels, Language]


class SubtitleStreamFormat(BaseStreamFormat):
    supported_options = [Codec, Language]


class TheoraStreamFormat(VideoStreamFormat):
    encoders = {'copy': VideoCopy,
                'theora': Theora}
    default_encoder = 'theora'
    name = 'theora'


class DivxStreamFormat(VideoStreamFormat):
    encoders = {'copy': VideoCopy,
                'divx': Divx}
    default_encoder = 'divx'
    name = 'divx'


class Vp8StreamFormat(VideoStreamFormat):
    encoders = {'copy': VideoCopy,
                'vp8': Vp8}
    default_encoder = 'vp8'
    name = 'vp8'


class H263StreamFormat(VideoStreamFormat):
    encoders = {'copy': VideoCopy,
                'h263': H263}
    default_encoder = 'h263'
    name = 'h263'


class FlvStreamFormat(VideoStreamFormat):
    encoders = {'copy': VideoCopy,
                'flv': Flv}
    default_encoder = 'flv'
    name = 'flv'


class Mpeg1StreamFormat(VideoStreamFormat):
    encoders = {'copy': VideoCopy,
                'mpeg1': Mpeg1}
    default_encoder = 'mpeg1'
    name = 'mpeg1'


class Mpeg2StreamFormat(VideoStreamFormat):
    encoders = {'copy': VideoCopy,
                'mpeg2': Mpeg2}
    default_encoder = 'mpeg2'
    name = 'mpeg2'


class H264StreamFormat(VideoStreamFormat):
    encoders = {'copy': VideoCopy,
                'h264': H264,
                'h264qsv': H264QSV,
                'h264vaapi': H264VAAPI,
                'nvenc_h264': NVEncH264
                }

    default_encoder = 'h264'
    name = 'h264'


class H265StreamFormat(VideoStreamFormat):
    encoders = {'copy': VideoCopy,
                'h265': H265,
                'hevcsqv': HEVCQSV,
                'nvenc_h265': NVEncH265
                }

    default_encoder = 'h265'
    name = 'hevc'


class VorbisStreamFormat(AudioStreamFormat):
    encoders = {'copy': AudioCopy,
                'vorbis': Vorbis}
    default_encoder = 'vorbis'
    name = 'vorbis'


class Mp3StreamFormat(AudioStreamFormat):
    encoders = {'copy': AudioCopy,
                'mp3': Mp3}
    default_encoder = 'mp3'
    name = 'mp3'


class Mp2StreamFormat(AudioStreamFormat):
    encoders = {'copy': AudioCopy,
                'mp2': Mp2}
    default_encoder = 'mp2'
    name = 'mp2'


class Eac3StreamFormat(AudioStreamFormat):
    encoders = {'copy': AudioCopy,
                'eac3': EAc3}
    default_encoder = 'eac3'
    name = 'eac3'


class Ac3StreamFormat(AudioStreamFormat):
    encoders = {'copy': AudioCopy,
                'ac3': Ac3}
    default_encoder = 'ac3'
    name = 'ac3'


class DtsStreamFormat(AudioStreamFormat):
    encoders = {'copy': AudioCopy,
                'dts': Dts}
    default_encoder = 'dts'
    name = 'dts'


class FlacStreamFormat(AudioStreamFormat):
    encoders = {'copy': AudioCopy,
                'flac': Flac}
    default_encoder = 'flac'
    name = 'flac'


class AacStreamFormat(AudioStreamFormat):
    encoders = {'copy': AudioCopy,
                'aac': Aac,
                'fdkaac': FdkAac,
                'faac': Faac}

    default_encoder = 'aac'
    name = 'aac'


class MovtextStreamFormat(SubtitleStreamFormat):
    encoders = {'copy': AudioCopy,
                'mov_text': MOVText}
    default_encoder = 'mov_text'
    name = 'mov_text'


class SrtStreamFormat(SubtitleStreamFormat):
    encoders = {'copy': SubtitleCopy,
                'srt': Srt}
    default_encoder = 'srt'
    name = 'srt'


class SSAStreamFormat(SubtitleStreamFormat):
    encoders = {'copy': SubtitleCopy,
                'ssa': SSA}
    default_encoder = 'ssa'
    name = 'ssa'


class SubRipStreamFormat(SubtitleStreamFormat):
    encoders = {'copy': SubtitleCopy,
                'subrip': SubRip}
    default_encoder = 'subrip'
    name = 'subrip'


class DvdSubStreamFormat(SubtitleStreamFormat):
    encoders = {'copy': SubtitleCopy,
                'dvdsub': DVDSub}
    default_encoder = 'dvdsub'
    name = 'dvdsub'


class DVBSubStreamFormat(SubtitleStreamFormat):
    encoders = {'copy': SubtitleCopy,
                'dvbsub': DVBSub}
    default_encoder = 'dvbsub'
    name = 'dvbsub'


class WebVTTStreamFormat(SubtitleStreamFormat):
    encoders = {'copy': SubtitleCopy,
                'webvtt': WebVTT}
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
        'ass': SSAStreamFormat,
        'subrip': SubRipStreamFormat,
        'dvdsub': DvdSubStreamFormat,
        'dvbsub': DVBSubStreamFormat,
        'webvtt': WebVTTStreamFormat,
        'videocopy': VideoCopy,
        'audiocopy': AudioCopy,
        'subtitlecopy': SubtitleCopy
    }

    @classmethod
    def get_format(cls, fmt: str):
        if fmt.lower() not in cls.formats:
            raise MissingFormatExcetption(
                f'Format {fmt} is unsupported. Available formats are {", ".join(cls.formats.keys())}')

        return cls.formats[fmt.lower()]


class MissingFormatExcetption(Exception):
    pass
