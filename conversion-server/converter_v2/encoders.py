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
    produces = ''
    score = 5

    def __init__(self):
        self.options = Options()

    def add_option(self, *options: Union[IStreamOption, IStreamValueOption, EncoderOption]):

        for option in options:
            assert isinstance(option, (IStreamOption, IStreamValueOption, EncoderOption))
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
    supported_options.extend([Bitrate, Disposition, Bsf])
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


class VideoCopy(_Copy):
    codec_type = 'video'
    supported_options = _VideoCodec.supported_options.copy()


class AudioCopy(_Copy):
    codec_type = 'audio'
    supported_options = _AudioCodec.supported_options.copy()


class SubtitleCopy(_Copy):
    codec_type = 'subtitle'
    supported_options = _SubtitleCodec.supported_options.copy()


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

    def __init__(self):
        super(H265, self).__init__()
        self.options.add_option(Tag('hvc1'))


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
    ffmpeg_codec_name = 'hdmv_pgs_subtitle'
    produces = 'hdmv_pgs_subtitle'
    supported_options = _SubtitleCodec.supported_options.copy()


class EncoderFactory(object):
    supported_codecs = [VideoCopy, AudioCopy, SubtitleCopy,
                        Vorbis, Aac, FdkAac, Faac, Ac3, EAc3, Flac, Dts, Mp2, Mp3,
                        Theora, H264, NVEncH264, H264QSV, H264VAAPI, H265, NVEncH265, HEVCQSV, Divx, Vp8, H263, Flv,
                        Mpeg1, Mpeg2,
                        MOVText, WebVTT, SSA, SubRip, DVBSub, DVDSub, Pgs]

    @classmethod
    def get_codec_by_name(cls, name: str, *options: Union[IStreamOption, IStreamValueOption]):
        try:
            codec_class = next(cdc for cdc in cls.supported_codecs if cdc.__name__.lower() == name.lower())
        except StopIteration:
            log.error('Could not find codec %s', name)
            return None
        else:
            return codec_class(*options)

    @classmethod
    def is_supported(cls, name):
        if name == 'copy':
            return True
        return (name in [enc.codec_name for enc in cls.supported_codecs] or
                name in [enc.ffmpeg_codec_name for enc in cls.supported_codecs])


class Encoders(object):

    def __init__(self, ffmpeg_path, ffprobe_path):
        from converter_v2.ffmpeg import FFMpeg
        ff = FFMpeg(ffmpeg_path, ffprobe_path)
        self.available_encoders = ff.encoders
        self.available_decoders = ff.decoders

        self.encoder_format = {}

        for enc in EncoderFactory.supported_codecs:
            if enc.produces in self.encoder_format and self.is_ffmpeg_supported(enc):
                self.encoder_format[enc.produces].append(enc)

            elif not self.is_ffmpeg_supported(enc):
                print(f'Encoder {enc.codec_name} not supported by ffmpeg')
                log.debug(f'Encoder {enc.ffmpeg_codec_name} not supported by ffmpeg')

            else:
                self.encoder_format[enc.produces] = [enc]

    def is_ffmpeg_encoder(self, encoder: _FFMpegCodec):
        if encoder.ffmpeg_codec_name == 'copy':
            return True
        else:
            return encoder.ffmpeg_codec_name in self.available_encoders

    def is_ffmpeg_decoder(self, decoder: _FFMpegCodec):
        return decoder.ffmpeg_codec_name in self.available_decoders

    def is_ffmpeg_supported(self, codec: _FFMpegCodec):
        if codec.ffmpeg_codec_name == 'copy':
            return True
        else:
            return (codec.codec_name in self.available_encoders or
                    codec.codec_name in self.available_decoders)

    def get_encoder_from_stream_format(self, streamformat):
        if streamformat in self.encoder_format:
            if len(self.encoder_format[streamformat]) == 1:
                return self.encoder_format[streamformat][0]
            elif len(self.encoder_format[streamformat]) > 1:
                return self.get_best_encoder(self.encoder_format[streamformat])
        else:
            log.warning(f'Could not find encoder to produce format {streamformat}')
            return None

    def get_best_encoder(self, encoders):
        l = sorted(encoders, key=lambda enc: enc.score, reverse=True)
        return l[0]

if __name__ == '__main__':
    e = Encoders('/usr/local/bin/ffmpeg', '/usr/local/bin/ffprobe')
    enc = e.get_encoder_from_stream_format('hevc')
    print('yeha')