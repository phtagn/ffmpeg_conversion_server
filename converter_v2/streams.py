from typing import Optional
from converter_v2.streamoptions import *
import logging

log = logging.getLogger(__name__)


class Stream(object):
    supported_options = []

    def __init__(self, options: list):
        self._options = []
        if options:
            for opt in options:
                self.add_option(opt)

    def add_option(self, opt):
        if type(opt) in self.supported_options:
            self._options.append(opt)
            setattr(self, opt.name, opt)

    @property
    def options(self):
        return self._options


class VideoStream(Stream):
    supported_options = [Codec, PixFmt, Bitrate, Disposition, Height, Width, Level, Profile]

    def __init__(self, options):
        super(VideoStream, self).__init__(options)


class AudioStream(Stream):
    supported_options = [Codec, Channels, Language, Disposition, Bitrate]

    def __init__(self, options):
        super(AudioStream, self).__init__(options)


class SubtitleStream(Stream):
    supported_options = [Codec, Language, Disposition]

    def __init__(self, options):
        super(SubtitleStream, self).__init__(options)


class Container(object):
    supported_formats = ['mp4', 'matroska']

    def __init__(self, fmt):
        if fmt in self.supported_formats:
            self.format = fmt
            self._streams = {}

        else:
            raise Exception('Format %s not supported', fmt)

    def add_stream(self, stream: Union[AudioStream, VideoStream, SubtitleStream], stream_number: Optional[int] = 0):
        assert isinstance(stream, (VideoStream, AudioStream, SubtitleStream))
        if stream_number:
            sn = stream_number
        else:
            sn = len(self._streams)
            sn += 1 if sn > 0 else 0
        if stream_number in self._streams.keys():
            log.info('Replacing stream %s', stream_number)

        self._streams.update({sn: stream})

    @property
    def audio_streams(self):
        return {k: v for k, v in self._streams.items() if isinstance(v, AudioStream)}

    @property
    def subtitle_streams(self):
        return {k: v for k, v in self._streams.items() if isinstance(v, SubtitleStream)}

    @property
    def video_streams(self):
        return {k: v for k, v in self._streams.items() if isinstance(v, VideoStream)}

    def get_stream(self, index):
        if index in self._streams:
            return self._streams[index]
        else:
            raise Exception('No such stream %s', index)


def ContainerFromFFprobe(filepath, ffmpegpath, ffprobepath) -> Container:
    from converter_v2 import ffmpeg

    ff = ffmpeg.FFMpeg(ffmpegpath, ffprobepath)
    parser = ff.probe(filepath)


    if 'matroska' in parser.format:
        ctn = Container('matroska')
    elif 'mp4' in parser.format:
        ctn = Container('mp4')
    else:
        ctn = Container(parser.format)

    for idx in range(len(parser.streams)):

        if parser.codec_type(idx) == 'video':
            v = VideoStream([parser.codec(idx),
                             parser.pix_fmt(idx),
                             parser.height(idx),
                             parser.width(idx),
                             parser.bitrate(idx),
                             parser.disposition(idx),
                             parser.level(idx),
                             parser.profile(idx)])
            ctn.add_stream(v, idx)

        elif parser.codec_type(idx) == 'audio':
            a = AudioStream([parser.codec(idx),
                             parser.channels(idx),
                             parser.language(idx),
                             parser.bitrate(idx),
                             parser.disposition(idx)])
            ctn.add_stream(a, idx)

        elif parser.codec_type(idx) == 'subtitle':
            s = SubtitleStream([parser.codec(idx),
                                parser.language(idx),
                                parser.disposition(idx)])
            ctn.add_stream(s, idx)

    return ctn


class FromTo(object):

    def __init__(self, ctn: Container):
        self.container = ctn

    def build_target_container(self, template):
        pass

class VideoStreamTemplate(object):

    def __init__(self,
                 codecs,
                 default_codec,
                 height,
                 width,
                 bitrate,
                 level,
                 profiles,
                 pix_fmts):

        self.codecs = codecs
        self.height = height
        self.width = width
        self.bitrate = bitrate
        self.level = level
        self.profiles = profiles
        self.pix_fmts = pix_fmts
        self.default_codec = default_codec

    def build_videostream(self, vstream: VideoStream):
        if vstream.options[Codec].value not in self.codecs:
            cdc = Codec(self.default_codec)
        else:
            cdc = self


if __name__ == '__main__':
    ctn = ContainerFromFFprobe("/Users/jon/Downloads/Geostorm 2017 1080p FR EN X264 AC3-mHDgz.mkv", '/usr/local/bin/ffmpeg', '/usr/local/bin/ffprobe')


    print('yeah')
