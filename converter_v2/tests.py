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

    @property
    def options(self):
        return self._options


class VideoStream(Stream):
    supported_options = [Codec, PixFmt, Bitrate, Disposition]

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

    for index in range(len(parser.streams)):
        pass


if __name__ == '__main__':
    lang = Language('a', 'fre')
    channels = Channels('a', 5)
    aud = AudioStream([lang, channels])
    Ctn = Container('mp4')

    Ctn.add_stream(aud)
    print('yeah')
