#!/usr/bin/env python
from converter.streamoptions import *
from typing import Union, List
from abc import ABC

"""
converter.encoders.py
Contains all encoders supported by the program. Encoders are designed to be the last step in the preparation process. 
Options that have been determined by the program are added to the relevant encoder, and the encoder is then parsed to
obtain a list of options that can be fed to Popen and ffmpeg.
"""
log = logging.getLogger(__name__)


class _FFMpegCodec(ABC):
    """
    Base audio/video codec class.
    """
    codec_name = None
    ffmpeg_codec_name = None
    supported_options = [Filter]
    codec_type = ''
    produces = ''
    score = 5

    def __init__(self):
        self.options = Options()

    def add_option(self, *options: Union[IStreamOption, IStreamValueOption, EncoderOption, MetadataOption]):
        """
        Adds the option to the encoder.
        :param options: a decendent of IStreamOption, IStreamValueOption, EncoderOption or MetadataOption
        :type options: IStreamOption, IStreamValueOption, EncoderOption, MetadataOption
        :return:
        :rtype:
        """
        for option in options:
            assert isinstance(option, (IStreamOption, IStreamValueOption, EncoderOption, MetadataOption))
            if type(option) in self.__class__.supported_options:
                self.options.add_option(option)
            else:
                log.error('Option "%s" with "value" %s is not supported by encoder "%s"', option.__class__.__name__,
                          option.value,
                          self.__class__.__name__)

    def parse(self, stream_number: int):
        if self.codec_type == 'video':
            stream_type = 'v'
        elif self.codec_type == 'audio':
            stream_type = 'a'
        elif self.codec_type == 'subtitle':
            stream_type = 's'

        ffmpeg_opt_list = [f'-c:{stream_type}:{stream_number}', self.ffmpeg_codec_name]

        for option in self.options.options:
            ffmpeg_opt_list.extend(option.parse(stream_type=self.codec_type, stream_number=stream_number))

        return ffmpeg_opt_list


class _VideoCodec(_FFMpegCodec):
    supported_options = _FFMpegCodec.supported_options.copy()
    supported_options.extend([Bitrate, Disposition, Bsf, Tag])
    codec_type = 'video'


class _AudioCodec(_FFMpegCodec):
    supported_options = _FFMpegCodec.supported_options.copy()
    supported_options.extend([Bitrate, Channels, Language, Disposition, Bsf])
    codec_type = 'audio'


class _SubtitleCodec(_FFMpegCodec):
    supported_options = _FFMpegCodec.supported_options.copy()
    supported_options.extend([Language, Disposition])
    codec_type = 'subtitle'


class _Copy(_FFMpegCodec):
    """
    Copy audio stream directly from the source.
    """
    codec_name = 'copy'
    ffmpeg_codec_name = 'copy'
    supported_options = [Bsf, Language, Disposition]


class VideoCopy(_Copy):
    codec_type = 'video'
    codec_name = 'video_copy'
    supported_options = _Copy.supported_options.copy()


class AudioCopy(_Copy):
    codec_type = 'audio'
    codec_name = 'audio_copy'
    supported_options = _Copy.supported_options.copy()


class SubtitleCopy(_Copy):
    codec_type = 'subtitle'
    codec_name = 'subtitle_copy'
    supported_options = _Copy.supported_options.copy()


class H264(_VideoCodec):
    """
    H.264/AVC video codec.
    """
    codec_name = 'h264'
    ffmpeg_codec_name = 'libx264'
    supported_options = _VideoCodec.supported_options.copy()
    supported_options.extend([PixFmt, Level, Profile, Bitrate, Disposition, Crf])
    produces = 'h264'


class Vorbis(_VideoCodec):
    """
    Vorbis audio codec.
    """
    codec_name = 'vorbis'
    produces = 'vorbis'
    ffmpeg_codec_name = 'libvorbis'
    supported_options = _VideoCodec.supported_options.copy()


class Aac(_AudioCodec):
    """
    AAC audio codec.
    """
    codec_name = 'aac'
    ffmpeg_codec_name = 'aac'
    supported_options = _AudioCodec.supported_options.copy()
    produces = 'aac'
    score = 5


class FdkAac(_AudioCodec):
    """
    AAC audio codec.
    """
    codec_name = 'libfdk_aac'
    ffmpeg_codec_name = 'libfdk_aac'
    produces = 'aac'
    score = 2
    supported_options = _AudioCodec.supported_options.copy()


class Faac(_AudioCodec):
    """
    AAC audio codec.
    """
    codec_name = 'libfaac'
    ffmpeg_codec_name = 'libfaac'
    produces = 'aac'
    score = 1
    supported_options = _AudioCodec.supported_options.copy()


class Ac3(_AudioCodec):
    """
    AC3 audio codec.
    """
    codec_name = 'ac3'
    ffmpeg_codec_name = 'ac3'
    produces = 'ac3'
    supported_options = _AudioCodec.supported_options.copy()


class EAc3(_AudioCodec):
    """
    Dolby Digital Plus/EAC3 audio codec.
    """
    codec_name = 'eac3'
    ffmpeg_codec_name = 'eac3'
    produces = 'eac3'
    supported_options = _AudioCodec.supported_options.copy()


class Flac(_AudioCodec):
    """
    FLAC audio codec.
    """
    codec_name = 'flac'
    ffmpeg_codec_name = 'flac'
    produces = 'flac'
    supported_options = _AudioCodec.supported_options.copy()


class Dts(_AudioCodec):
    """
    DTS audio codec.
    """
    codec_name = 'dts'
    ffmpeg_codec_name = 'dca'
    dca_experimental_enable = ['-strict', '-2']
    produces = 'dts'
    supported_options = _AudioCodec.supported_options.copy()


class Mp3(_AudioCodec):
    """
    MP3 (MPEG layer 3) audio codec.
    """
    codec_name = 'mp3'
    ffmpeg_codec_name = 'libmp3lame'
    produces = 'mp3'
    supported_options = _AudioCodec.supported_options.copy()


class Mp2(_AudioCodec):
    """
    MP2 (MPEG layer 2) audio codec.
    """
    codec_name = 'mp2'
    ffmpeg_codec_name = 'mp2'
    produces = 'mp2'
    supported_options = _AudioCodec.supported_options.copy()


# Video Codecs
class Theora(_VideoCodec):
    """
    Theora video codec.
    """
    codec_name = 'theora'
    ffmpeg_codec_name = 'libtheora'
    produces = 'theora'
    supported_options = _VideoCodec.supported_options.copy()


class NVEncH264(H264):
    """
    Nvidia H.264/AVC video codec.
    """
    codec_name = 'nvenc_h264'
    ffmpeg_codec_name = 'nvenc_h264'
    produces = 'h264'
    score = 1
    supported_options = _VideoCodec.supported_options.copy()


class H264VAAPI(H264):
    """
    H.264/AVC video codec.
    """
    codec_name = 'h264vaapi'
    ffmpeg_codec_name = 'h264_vaapi'
    produces = 'h264'
    score = 1
    supported_options = _VideoCodec.supported_options.copy()


class H264QSV(H264):
    """
    H.264/AVC video codec.
    """
    codec_name = 'h264qsv'
    ffmpeg_codec_name = 'h264_qsv'
    produces = 'h264'
    score = 1
    supported_options = _VideoCodec.supported_options.copy()


class H265(_VideoCodec):
    """
    H.265/AVC video codec.
    """
    codec_name = 'hevc'
    ffmpeg_codec_name = 'libx265'
    produces = 'hevc'
    supported_options = _VideoCodec.supported_options.copy()

    # def __init__(self):
    #    super(H265, self).__init__()
    #    self.options.add_option(Tag('hvc1'))


class HEVCQSV(H265):
    """
    HEVC video codec.
    """
    codec_name = 'hevcqsv'
    ffmpeg_codec_name = 'hevc_qsv'
    produces = 'hevc'
    score = 1
    supported_options = _VideoCodec.supported_options.copy()


class NVEncH265(H265):
    """
    Nvidia H.265/AVC video codec.
    """
    codec_name = 'nvenc_h265'
    ffmpeg_codec_name = 'hevc_nvenc'
    produces = 'hevc'
    score = 1
    supported_options = _VideoCodec.supported_options.copy()


class Divx(_VideoCodec):
    """
    DivX video codec.
    """
    codec_name = 'divx'
    ffmpeg_codec_name = 'mpeg4'
    produces = 'divx'
    supported_options = _VideoCodec.supported_options.copy()


class Vp8(_VideoCodec):
    """
    Google VP8 video codec.
    """
    codec_name = 'vp8'
    ffmpeg_codec_name = 'libvpx'
    produces = 'vp8'
    supported_options = _VideoCodec.supported_options.copy()


class H263(_VideoCodec):
    """
    H.263 video codec.
    """
    codec_name = 'h263'
    ffmpeg_codec_name = 'h263'
    produces = 'h263'
    supported_options = _VideoCodec.supported_options.copy()


class Flv(_VideoCodec):
    """
    Flash Video codec.
    """
    codec_name = 'flv'
    ffmpeg_codec_name = 'flv'
    produces = 'flv'
    supported_options = _VideoCodec.supported_options.copy()


class Mpeg1(_VideoCodec):
    """
    MPEG-1 video codec.
    """
    codec_name = 'mpeg1'
    ffmpeg_codec_name = 'mpeg1video'
    produces = 'mpeg1'
    supported_options = _VideoCodec.supported_options.copy()


class Mpeg2(_VideoCodec):
    """
    MPEG-2 video codec.
    """
    codec_name = 'mpeg2'
    ffmpeg_codec_name = 'mpeg2video'
    produces = 'mpeg2'
    supported_options = _VideoCodec.supported_options.copy()


# Subtitle Codecs
class MOVText(_SubtitleCodec):
    """
    mov_text subtitle codec.
    """
    codec_name = 'mov_text'
    ffmpeg_codec_name = 'mov_text'
    produces = 'mov_text'
    supported_options = _SubtitleCodec.supported_options.copy()


class Srt(_SubtitleCodec):
    """
    SRT subtitle codec.
    """
    codec_name = 'srt'
    ffmpeg_codec_name = 'srt'
    produces = 'srt'
    supported_options = _SubtitleCodec.supported_options.copy()


class WebVTT(_SubtitleCodec):
    """
    SRT subtitle codec.
    """
    codec_name = 'webvtt'
    ffmpeg_codec_name = 'webvtt'
    produces = 'webvtt'
    supported_options = _SubtitleCodec.supported_options.copy()


class SSA(_SubtitleCodec):
    """
    SSA (SubStation Alpha) subtitle.
    """
    codec_name = 'ass'
    ffmpeg_codec_name = 'ass'
    produces = 'ssa'
    supported_options = _SubtitleCodec.supported_options.copy()


class SubRip(_SubtitleCodec):
    """
    SubRip subtitle.
    """
    codec_name = 'subrip'
    ffmpeg_codec_name = 'subrip'
    produces = 'subrip'
    supported_options = _SubtitleCodec.supported_options.copy()


class DVBSub(_SubtitleCodec):
    """
    DVB subtitles.
    """
    codec_name = 'dvbsub'
    ffmpeg_codec_name = 'dvbsub'
    produces = 'dvdsub'
    supported_options = _SubtitleCodec.supported_options.copy()


class DVDSub(_SubtitleCodec):
    """
    DVD subtitles.
    """
    codec_name = 'dvdsub'
    ffmpeg_codec_name = 'dvdsub'
    produces = 'dvbsub'
    supported_options = _SubtitleCodec.supported_options.copy()


class Pgs(_SubtitleCodec):
    codec_name = 'hdmv_pgs_subtitle'
    ffmpeg_codec_name = 'pgssub'
    produces = 'hdmv_pgs_subtitle'
    supported_options = _SubtitleCodec.supported_options.copy()


class Encoders(object):
    _supported_codecs = [VideoCopy, AudioCopy, SubtitleCopy,
                         Vorbis, Aac, FdkAac, Faac, Ac3, EAc3, Flac, Dts, Mp2, Mp3,
                         Theora, H264, NVEncH264, H264QSV, H264VAAPI, H265, NVEncH265, HEVCQSV, Divx, Vp8, H263, Flv,
                         Mpeg1, Mpeg2,
                         MOVText, WebVTT, SSA, SubRip, DVBSub, DVDSub, Pgs]

    def __init__(self, ffmpeg):
        self._available_encoders = ffmpeg.encoders
        self._available_decoders = ffmpeg.decoders
        self.supported_codecs = [cdc for cdc in self.__class__._supported_codecs if
                                 cdc.ffmpeg_codec_name in ffmpeg.encoders]
        self.supported_codecs.extend([VideoCopy, AudioCopy, SubRip])

    def is_ffmpeg_encoder(self, enc):
        return enc in self._available_encoders

    @classmethod
    def is_supported(cls, name):
        if name == 'copy':
            return True
        return (name in [enc.codec_name for enc in cls._supported_codecs] or
                name in [enc.ffmpeg_codec_name for enc in cls._supported_codecs])


class EncoderFactory(object):

    def __init__(self, encoders: Encoders, defaults=None):
        self.defaults = {} if defaults is None else defaults
        self.encoders = encoders

    def get_encoder(self, source_stream, target_stream):
        """

        :param source_stream:
        :type source_stream: converter.streams.Stream
        :param target_stream:
        :type target_stream: converter.streams.Stream
        :return:
        :rtype:
        """
        assert source_stream.__class__ == target_stream.__class__
        if source_stream == target_stream:
            if source_stream.kind == 'video':
                return VideoCopy()
            elif source_stream.kind == 'audio':
                return AudioCopy()
            elif source_stream.kind == 'subtitle':
                return SubtitleCopy()
        else:
            encoder = self._get_best_encoder(target_stream.codec.value)
            if encoder.codec_name in self.defaults:
                for opt in self.defaults[encoder.codec_name]:
                    encoder.add_option(opt)

            return encoder

    def _get_best_encoder(self, stream_format):
        matching_encoder = [cdc for cdc in self.encoders.supported_codecs if cdc.produces == stream_format]
        return sorted(matching_encoder, key=lambda enc: enc.score, reverse=True)[0]()

    def get_codec_by_name(self, name: str):
        try:
            codec_class = next(cdc for cdc in self.encoders.supported_codecs if cdc.codec_name == name.lower())
        except StopIteration:
            log.error('Could not find codec %s', name)
            return None
        else:
            return codec_class()
