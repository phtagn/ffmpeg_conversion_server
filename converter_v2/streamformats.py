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


class VideoStream(BaseStreamFormat):
    supported_options = [Height, Width, Codec, Bitrate, PixFmt]


class AudioStream(BaseStreamFormat):
    supported_options = [Codec, Bitrate, Channels, Language]


class SubtitleStream(BaseStreamFormat):
    supported_options = [Codec, Language]


class TheoraStream(VideoStream):
    encoders = {'copy': VideoCopy,
                'theora': Theora}
    default_encoder = 'theora'
    name = 'theora'


class DivxStream(VideoStream):
    encoders = {'copy': VideoCopy,
                'divx': Divx}
    default_encoder = 'divx'
    name = 'divx'


class Vp8Stream(VideoStream):
    encoders = {'copy': VideoCopy,
                'vp8': Vp8}
    default_encoder = 'vp8'
    name = 'vp8'


class H263Stream(VideoStream):
    encoders = {'copy': VideoCopy,
                'h263': H263}
    default_encoder = 'h263'
    name = 'h263'


class FlvStream(VideoStream):
    encoders = {'copy': VideoCopy,
                'flv': Flv}
    default_encoder = 'flv'
    name = 'flv'


class Mpeg1Stream(VideoStream):
    encoders = {'copy': VideoCopy,
                'mpeg1': Mpeg1}
    default_encoder = 'mpeg1'
    name = 'mpeg1'


class Mpeg2Stream(VideoStream):
    encoders = {'copy': VideoCopy,
                'mpeg2': Mpeg2}
    default_encoder = 'mpeg2'
    name = 'mpeg2'


class H264Stream(VideoStream):
    encoders = {'copy': VideoCopy,
                'h264': H264,
                'h264qsv': H264QSV,
                'h264vaapi': H264VAAPI,
                'nvenc_h264': NVEncH264
                }
    supported_options = VideoStream.supported_options
    supported_options.extend([Profile, Level])
    default_encoder = 'h264'
    name = 'h264'


class H265Stream(VideoStream):
    encoders = {'copy': VideoCopy,
                'h265': H265,
                'hevcsqv': HEVCQSV,
                'nvenc_h265': NVEncH265
                }

    default_encoder = 'h265'
    name = 'hevc'


class VorbisStream(AudioStream):
    encoders = {'copy': AudioCopy,
                'vorbis': Vorbis}
    default_encoder = 'vorbis'
    name = 'vorbis'


class Mp3Stream(AudioStream):
    encoders = {'copy': AudioCopy,
                'mp3': Mp3}
    default_encoder = 'mp3'
    name = 'mp3'


class Mp2Stream(AudioStream):
    encoders = {'copy': AudioCopy,
                'mp2': Mp2}
    default_encoder = 'mp2'
    name = 'mp2'


class Eac3Stream(AudioStream):
    encoders = {'copy': AudioCopy,
                'eac3': EAc3}
    default_encoder = 'eac3'
    name = 'eac3'


class Ac3Stream(AudioStream):
    encoders = {'copy': AudioCopy,
                'ac3': Ac3}
    default_encoder = 'ac3'
    name = 'ac3'


class DtsStream(AudioStream):
    encoders = {'copy': AudioCopy,
                'dts': Dts}
    default_encoder = 'dts'
    name = 'dts'


class FlacStream(AudioStream):
    encoders = {'copy': AudioCopy,
                'flac': Flac}
    default_encoder = 'flac'
    name = 'flac'


class AacStream(AudioStream):
    encoders = {'copy': AudioCopy,
                'aac': Aac,
                'fdkaac': FdkAac,
                'faac': Faac}

    default_encoder = 'aac'
    name = 'aac'


class MovtextStream(SubtitleStream):
    encoders = {'copy': AudioCopy,
                'mov_text': MOVText}
    default_encoder = 'mov_text'
    name = 'mov_text'


class SrtStream(SubtitleStream):
    encoders = {'copy': SubtitleCopy,
                'srt': Srt}
    default_encoder = 'srt'
    name = 'srt'


class SSAStream(SubtitleStream):
    encoders = {'copy': SubtitleCopy,
                'ssa': SSA}
    default_encoder = 'ssa'
    name = 'ssa'


class SubRipStream(SubtitleStream):
    encoders = {'copy': SubtitleCopy,
                'subrip': SubRip}
    default_encoder = 'subrip'
    name = 'subrip'


class DvdSubStream(SubtitleStream):
    encoders = {'copy': SubtitleCopy,
                'dvdsub': DVDSub}
    default_encoder = 'dvdsub'
    name = 'dvdsub'


class DVBSubStream(SubtitleStream):
    encoders = {'copy': SubtitleCopy,
                'dvbsub': DVBSub}
    default_encoder = 'dvbsub'
    name = 'dvbsub'


class WebVTTStream(SubtitleStream):
    encoders = {'copy': SubtitleCopy,
                'webvtt': WebVTT}
    default_encoder = 'webvtt'
    name = 'webvtt'


class StreamFormatFactory(object):
    formats = {
        'theora': TheoraStream,
        'h264': H264Stream,
        'x264': H264Stream,  # Alias
        'h265': H265Stream,
        'hevc': H265Stream,  # Alias
        'divx': DivxStream,
        'vp8': Vp8Stream,
        'h263': H263Stream,
        'flv': FlvStream,
        'mpeg1': Mpeg1Stream,
        'mpeg2': Mpeg2Stream,

        'vorbis': VorbisStream,
        'aac': AacStream,
        'mp3': Mp3Stream,
        'mp2': Mp2Stream,
        'ac3': Ac3Stream,
        'eac3': Eac3Stream,
        'dts': DtsStream,
        'flac': FlacStream,

        'mov_text': MovtextStream,
        'srt': SrtStream,
        'ssa': SSAStream,
        'ass': SSAStream,
        'subrip': SubRipStream,
        'dvdsub': DvdSubStream,
        'dvbsub': DVBSubStream,
        'webvtt': WebVTTStream,

    }

    @classmethod
    def get_format(cls, fmt: str):
        if fmt.lower() not in cls.formats:
            raise MissingFormatExcetption(
                f'Format {fmt} is unsupported. Available formats are {", ".join(cls.formats.keys())}')

        return cls.formats[fmt.lower()]


class MissingFormatExcetption(Exception):
    pass
