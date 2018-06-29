#!/usr/bin/env python
from converter_v2.streamoptions import *
from typing import Union
from abc import ABC

log = logging.getLogger(__name__)


class _FFMpegCodec(ABC):
    """
    Base audio/video codec class.
    """
    codec_name = None
    ffmpeg_codec_name = None
    supported_options = [Map]
    codec_type = ''

    def __init__(self, *options: Union[IStreamOption, IStreamValueOption, EncoderOption]):
        self.options = []
        self.add_option(*options)

    def add_option(self, *options: Union[IStreamOption, IStreamValueOption, EncoderOption]):

        for option in options:
            assert isinstance(option, (IStreamOption, IStreamValueOption, EncoderOption))
            if type(option) in self.__class__.supported_options:
                self.options.append(option)
            else:
                pass
                # log.error('Option %s is not supported', option.__name__)

    def parse(self, stream_number: int):
        if self.codec_type == 'video':
            stream_type = 'v'
        elif self.codec_type == 'audio':
            stream_type = 'a'
        elif self.codec_type == 'subtitle':
            stream_type = 's'

        ffmpeg_opt_list = [f'-c:{stream_type}:{stream_number}', self.ffmpeg_codec_name]

        for option in self.options:
            ffmpeg_opt_list.extend(option.parse(stream_type=self.codec_type, stream_number=stream_number))

        return ffmpeg_opt_list


class _VideoCodec(_FFMpegCodec):
    supported_options = _FFMpegCodec.supported_options.copy()
    supported_options.extend([Disposition, Bsf])
    codec_type = 'video'

    def __init__(self, *options):
        super(_VideoCodec, self).__init__(*options)


class _AudioCodec(_FFMpegCodec):
    supported_options = _FFMpegCodec.supported_options.copy()
    supported_options.extend([Channels, Language, Disposition, Bsf])
    codec_type = 'audio'

    def __init__(self, *options):
        super(_AudioCodec, self).__init__(*options)


class _SubtitleCodec(_FFMpegCodec):
    supported_options = _FFMpegCodec.supported_options.copy()
    supported_options.extend([Language, Disposition])
    codec_type = 'subtitle'

    def __init__(self, *options):
        super(_SubtitleCodec, self).__init__(*options)


class _Copy(_FFMpegCodec):
    """
    Copy audio stream directly from the source.
    """
    codec_name = 'copy'
    ffmpeg_codec_name = 'copy'

    def __init__(self, *options):
        super(_Copy, self).__init__(*options)


class VideoCopy(_Copy):
    codec_type = 'video'
    supported_options = _VideoCodec.supported_options


class AudioCopy(_Copy):
    codec_type = 'audio'
    supported_options = _AudioCodec.supported_options


class SubtitleCopy(_Copy):
    codec_type = 'subtitle'
    supported_options = _SubtitleCodec.supported_options


class H264(_VideoCodec):
    """
    H.264/AVC video codec.
    """
    codec_name = 'h264'
    ffmpeg_codec_name = 'libx264'
    supported_options = _VideoCodec.supported_options
    supported_options.extend([PixFmt, Level, Profile, Bitrate, Disposition, Crf])


class Vorbis(_VideoCodec):
    """
    Vorbis audio codec.
    """
    codec_name = 'vorbis'
    ffmpeg_codec_name = 'libvorbis'
    supported_options = _VideoCodec.supported_options


class Aac(_AudioCodec):
    """
    AAC audio codec.
    """
    codec_name = 'aac'
    ffmpeg_codec_name = 'aac'
    supported_options = _AudioCodec.supported_options.copy()

class FdkAac(_AudioCodec):
    """
    AAC audio codec.
    """
    codec_name = 'libfdk_aac'
    ffmpeg_codec_name = 'libfdk_aac'


class Faac(_AudioCodec):
    """
    AAC audio codec.
    """
    codec_name = 'libfaac'
    ffmpeg_codec_name = 'libfaac'


class Ac3(_AudioCodec):
    """
    AC3 audio codec.
    """
    codec_name = 'ac3'
    ffmpeg_codec_name = 'ac3'


class EAc3(_AudioCodec):
    """
    Dolby Digital Plus/EAC3 audio codec.
    """
    codec_name = 'eac3'
    ffmpeg_codec_name = 'eac3'


class Flac(_AudioCodec):
    """
    FLAC audio codec.
    """
    codec_name = 'flac'
    ffmpeg_codec_name = 'flac'


class Dts(_AudioCodec):
    """
    DTS audio codec.
    """
    codec_name = 'dts'
    ffmpeg_codec_name = 'dca'
    dca_experimental_enable = ['-strict', '-2']


class Mp3(_AudioCodec):
    """
    MP3 (MPEG layer 3) audio codec.
    """
    codec_name = 'mp3'
    ffmpeg_codec_name = 'libmp3lame'


class Mp2(_AudioCodec):
    """
    MP2 (MPEG layer 2) audio codec.
    """
    codec_name = 'mp2'
    ffmpeg_codec_name = 'mp2'


# Video Codecs
class Theora(_VideoCodec):
    """
    Theora video codec.
    """
    codec_name = 'theora'
    ffmpeg_codec_name = 'libtheora'


class NVEncH264(H264):
    """
    Nvidia H.264/AVC video codec.
    """
    codec_name = 'nvenc_h264'
    ffmpeg_codec_name = 'nvenc_h264'


class H264VAAPI(H264):
    """
    H.264/AVC video codec.
    """
    codec_name = 'h264vaapi'
    ffmpeg_codec_name = 'h264_vaapi'


class H264QSV(H264):
    """
    H.264/AVC video codec.
    """
    codec_name = 'h264qsv'
    ffmpeg_codec_name = 'h264_qsv'


class H265(_VideoCodec):
    """
    H.265/AVC video codec.
    """
    codec_name = 'hevc'
    ffmpeg_codec_name = 'libx265'


class HEVCQSV(H265):
    """
    HEVC video codec.
    """
    codec_name = 'hevcqsv'
    ffmpeg_codec_name = 'hevc_qsv'


class NVEncH265(H265):
    """
    Nvidia H.265/AVC video codec.
    """
    codec_name = 'nvenc_h265'
    ffmpeg_codec_name = 'hevc_nvenc'


class Divx(_VideoCodec):
    """
    DivX video codec.
    """
    codec_name = 'divx'
    ffmpeg_codec_name = 'mpeg4'


class Vp8(_VideoCodec):
    """
    Google VP8 video codec.
    """
    codec_name = 'vp8'
    ffmpeg_codec_name = 'libvpx'


class H263(_VideoCodec):
    """
    H.263 video codec.
    """
    codec_name = 'h263'
    ffmpeg_codec_name = 'h263'


class Flv(_VideoCodec):
    """
    Flash Video codec.
    """
    codec_name = 'flv'
    ffmpeg_codec_name = 'flv'


class Mpeg1(_VideoCodec):
    """
    MPEG-1 video codec.
    """
    codec_name = 'mpeg1'
    ffmpeg_codec_name = 'mpeg1video'


class Mpeg2(_VideoCodec):
    """
    MPEG-2 video codec.
    """
    codec_name = 'mpeg2'
    ffmpeg_codec_name = 'mpeg2video'


# Subtitle Codecs
class MOVText(_SubtitleCodec):
    """
    mov_text subtitle codec.
    """
    codec_name = 'mov_text'
    ffmpeg_codec_name = 'mov_text'


class Srt(_SubtitleCodec):
    """
    SRT subtitle codec.
    """
    codec_name = 'srt'
    ffmpeg_codec_name = 'srt'


class WebVTT(_SubtitleCodec):
    """
    SRT subtitle codec.
    """
    codec_name = 'webvtt'
    ffmpeg_codec_name = 'webvtt'


class SSA(_SubtitleCodec):
    """
    SSA (SubStation Alpha) subtitle.
    """
    codec_name = 'ass'
    ffmpeg_codec_name = 'ass'


class SubRip(_SubtitleCodec):
    """
    SubRip subtitle.
    """
    codec_name = 'subrip'
    ffmpeg_codec_name = 'subrip'


class DVBSub(_SubtitleCodec):
    """
    DVB subtitles.
    """
    codec_name = 'dvbsub'
    ffmpeg_codec_name = 'dvbsub'


class DVDSub(_SubtitleCodec):
    """
    DVD subtitles.
    """
    codec_name = 'dvdsub'
    ffmpeg_codec_name = 'dvdsub'


class CodecFactory(object):
    supported_codecs = [VideoCopy, AudioCopy, SubtitleCopy, Vorbis, Aac, H264, Ac3]

    @classmethod
    def get_codec_by_name(cls, name: str, *options: Union[IStreamOption, IStreamValueOption]):
        try:
            codec_class = next(cdc for cdc in cls.supported_codecs if cdc.__name__.lower() == name.lower())
        except StopIteration:
            log.error('Could not find codec %s', name)
            return None
        else:
            return codec_class(*options)


if __name__ == '__main__':
    chan = OptionFactory.get_option('channels')('a', 5)
    toto = Vorbis([chan])
    lan = OptionFactory.get_option('language')('a', 'fre')
    toto.add_option(lan)

    print('Yeah')
