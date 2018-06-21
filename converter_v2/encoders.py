#!/usr/bin/env python
from converter_v2.streamoptions import *
log = logging.getLogger(__name__)


class FFMpegCodec(object):
    """
    Base audio/video codec class.
    """
    codec_name = None
    ffmpeg_codec_name = None
    supported_options = []

    def __init__(self, options: list):
        self.options = []
        for opt in options:
            self.add_option(opt)

    def add_option(self, option):

        #assert isinstance(option)

        if type(option) in self.__class__.supported_options:
            self.options.append(option)
        else:
            log.error('Option %s is not supported', option.name)


class VideoCodec(FFMpegCodec):
    supported_options = []
    codec_type = 'video'

    def __init__(self, options):
        super(VideoCodec, self).__init__(options)


class AudioCodec(FFMpegCodec):
    supported_options = [Channels]
    codec_type = 'audio'

    def __init__(self, options):
        super(AudioCodec, self).__init__(options)


class SubtitleCodec(FFMpegCodec):
    supported_options = []
    codec_type = 'subtitle'

    def __init__(self, options):
        super(SubtitleCodec, self).__init__(options)

class CopyCodec(FFMpegCodec):
    """
    Copy audio stream directly from the source.
    """
    codec_name = 'copy'
    ffmpeg_codec_name = 'copy'

    def __init__(self, options):
        super(CopyCodec, self).__init__(options)

class VorbisCodec(AudioCodec):
    """
    Vorbis audio codec.
    """
    codec_name = 'vorbis'
    ffmpeg_codec_name = 'libvorbis'
    supported_options = AudioCodec.supported_options.copy()
    supported_options.append(Language)

    def __init__(self, options):
        super(VorbisCodec, self).__init__(options)

class AacCodec(AudioCodec):
    """
    AAC audio codec.
    """
    codec_name = 'aac'
    ffmpeg_codec_name = 'aac'


class FdkAacCodec(AudioCodec):
    """
    AAC audio codec.
    """
    codec_name = 'libfdk_aac'
    ffmpeg_codec_name = 'libfdk_aac'


class FAacCodec(AudioCodec):
    """
    AAC audio codec.
    """
    codec_name = 'libfaac'
    ffmpeg_codec_name = 'libfaac'



class Ac3Codec(AudioCodec):
    """
    AC3 audio codec.
    """
    codec_name = 'ac3'
    ffmpeg_codec_name = 'ac3'


class EAc3Codec(AudioCodec):
    """
    Dolby Digital Plus/EAC3 audio codec.
    """
    codec_name = 'eac3'
    ffmpeg_codec_name = 'eac3'


class FlacCodec(AudioCodec):
    """
    FLAC audio codec.
    """
    codec_name = 'flac'
    ffmpeg_codec_name = 'flac'



class DtsCodec(AudioCodec):
    """
    DTS audio codec.
    """
    codec_name = 'dts'
    ffmpeg_codec_name = 'dca'
    dca_experimental_enable = ['-strict', '-2']


class Mp3Codec(AudioCodec):
    """
    MP3 (MPEG layer 3) audio codec.
    """
    codec_name = 'mp3'
    ffmpeg_codec_name = 'libmp3lame'




class Mp2Codec(AudioCodec):
    """
    MP2 (MPEG layer 2) audio codec.
    """
    codec_name = 'mp2'
    ffmpeg_codec_name = 'mp2'


# Video Codecs
class TheoraCodec(VideoCodec):
    """
    Theora video codec.
    """
    codec_name = 'theora'
    ffmpeg_codec_name = 'libtheora'


class H264Codec(VideoCodec):
    """
    H.264/AVC video codec.
    """
    codec_name = 'h264'
    ffmpeg_codec_name = 'libx264'


class X264(H264Codec):
    """
    Alias for H264
    """
    codec_name = 'x264'

    def __init__(self, opts) -> None:
        super(X264, self).__init__(opts)


class NVEncH264(H264Codec):
    """
    Nvidia H.264/AVC video codec.
    """
    codec_name = 'nvenc_h264'
    ffmpeg_codec_name = 'nvenc_h264'


class H264VAAPI(H264Codec):
    """
    H.264/AVC video codec.
    """
    codec_name = 'h264vaapi'
    ffmpeg_codec_name = 'h264_vaapi'


class H264QSV(H264Codec):
    """
    H.264/AVC video codec.
    """
    codec_name = 'h264qsv'
    ffmpeg_codec_name = 'h264_qsv'


class H265Codec(VideoCodec):
    """
    H.265/AVC video codec.
    """
    codec_name = 'hevc'
    ffmpeg_codec_name = 'libx265'


class HEVCQSV(H265Codec):
    """
    HEVC video codec.
    """
    codec_name = 'hevcqsv'
    ffmpeg_codec_name = 'hevc_qsv'


class NVEncH265(H265Codec):
    """
    Nvidia H.265/AVC video codec.
    """
    codec_name = 'nvenc_h265'
    ffmpeg_codec_name = 'hevc_nvenc'


class DivxCodec(VideoCodec):
    """
    DivX video codec.
    """
    codec_name = 'divx'
    ffmpeg_codec_name = 'mpeg4'


class Vp8Codec(VideoCodec):
    """
    Google VP8 video codec.
    """
    codec_name = 'vp8'
    ffmpeg_codec_name = 'libvpx'


class H263Codec(VideoCodec):
    """
    H.263 video codec.
    """
    codec_name = 'h263'
    ffmpeg_codec_name = 'h263'



class FlvCodec(VideoCodec):
    """
    Flash Video codec.
    """
    codec_name = 'flv'
    ffmpeg_codec_name = 'flv'



class Mpeg1Codec(VideoCodec):
    """
    MPEG-1 video codec.
    """
    codec_name = 'mpeg1'
    ffmpeg_codec_name = 'mpeg1video'

    def __init__(self, opts) -> None:
        super(Mpeg1Codec, self).__init__(opts)


class Mpeg2Codec(VideoCodec):
    """
    MPEG-2 video codec.
    """
    codec_name = 'mpeg2'
    ffmpeg_codec_name = 'mpeg2video'


# Subtitle Codecs
class MOVTextCodec(SubtitleCodec):
    """
    mov_text subtitle codec.
    """
    codec_name = 'mov_text'
    ffmpeg_codec_name = 'mov_text'


class SrtCodec(SubtitleCodec):
    """
    SRT subtitle codec.
    """
    codec_name = 'srt'
    ffmpeg_codec_name = 'srt'


class WebVTTCodec(SubtitleCodec):
    """
    SRT subtitle codec.
    """
    codec_name = 'webvtt'
    ffmpeg_codec_name = 'webvtt'

    def __init__(self, opts) -> None:
        super(WebVTTCodec, self).__init__(opts)


class SSA(SubtitleCodec):
    """
    SSA (SubStation Alpha) subtitle.
    """
    codec_name = 'ass'
    ffmpeg_codec_name = 'ass'

    def __init__(self, opts) -> None:
        super(SSA, self).__init__(opts)


class SubRip(SubtitleCodec):
    """
    SubRip subtitle.
    """
    codec_name = 'subrip'
    ffmpeg_codec_name = 'subrip'

    def __init__(self, opts) -> None:
        super(SubRip, self).__init__(opts)


class DVBSub(SubtitleCodec):
    """
    DVB subtitles.
    """
    codec_name = 'dvbsub'
    ffmpeg_codec_name = 'dvbsub'

    def __init__(self, opts) -> None:
        super(DVBSub, self).__init__(opts)


class DVDSub(SubtitleCodec):
    """
    DVD subtitles.
    """
    codec_name = 'dvdsub'
    ffmpeg_codec_name = 'dvdsub'

    def __init__(self, opts) -> None:
        super(DVDSub, self).__init__(opts)


if __name__ == '__main__':
    chan = OptionFactory.get_option('channels')('a', 5)
    toto = VorbisCodec([chan])
    lan = OptionFactory.get_option('language')('a', 'fre')
    toto.add_option(lan)

    print('Yeah')