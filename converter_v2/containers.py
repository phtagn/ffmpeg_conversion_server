import copy
from typing import Union, Optional, List
from converter_v2.encoders import SubtitleCopy
from converter_v2.streams import AudioStream, VideoStream, SubtitleStream
import logging

log = logging.getLogger(__name__)


class Container(object):
    supported_formats = ['mp4', 'matroska']

    def __init__(self, fmt):
        if fmt in self.supported_formats:
            self.format = fmt
            self._streams = {}

        else:
            raise Exception('Format %s not supported', fmt)

    def add_stream(self, stream: Union[AudioStream, VideoStream, SubtitleStream],
                   stream_number: Optional[int] = 0) -> int:
        """
        Add a stream to the list of streams in the Container. Streams can be with a specified stream
        number, or the method will insert at the next available stream number.
        :param stream: A concrete instance of Stream (VideoStream, AudioStream or SubtitleStream)
        :param stream_number: optional, insert the stream with the specified stream number
        :return: the stream number where the stream was inserted
        """
        assert isinstance(stream, (VideoStream, AudioStream, SubtitleStream))
        if stream_number:
            sn = stream_number
        else:
            sn = len(self._streams)
            sn += 1 if sn > 0 else 0
        if stream_number in self._streams.keys():
            log.info('Replacing stream %s', stream_number)

        self._streams.update({sn: stream})
        return sn

    @property
    def audio_streams(self):
        return {k: v for k, v in self._streams.items() if isinstance(v, AudioStream)}

    @property
    def subtitle_streams(self):
        return {k: v for k, v in self._streams.items() if isinstance(v, SubtitleStream)}

    @property
    def video_streams(self):
        return {k: v for k, v in self._streams.items() if isinstance(v, VideoStream)}

    @property
    def streams(self):
        return self._streams

    def get_stream(self, index) -> Optional[Union[VideoStream, AudioStream, SubtitleCopy]]:
        """
        Return the stream at the index, or None of the stream does not exist.
        :param index: int, the index of the stream
        :return: Stream
        """
        if index in self._streams:
            return self._streams.get(index, None)

    def __eq__(self, other):
        if isinstance(other, Container):
            if len(self.streams) != len(other.streams):
                return False

            for idx, stream in self.video_streams.items():
                if other.video_streams[idx] != stream:
                    return False

            for idx, stream in self.audio_streams.items():
                if other.audio_streams[idx] != stream:
                    return False

            for idx, stream in self.subtitle_streams.items():
                if other.subtitle_streams[idx] != stream:
                    return False

            return True

        return False


class ContainerFactory(object):

    @staticmethod
    def container_from_ffprobe(filepath, ffmpegpath, ffprobepath) -> Container:
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
                v = VideoStream(parser.codec(idx))
                v.add_options(parser.pix_fmt(idx),
                              parser.height(idx),
                              parser.width(idx),
                              parser.bitrate(idx),
                              parser.disposition(idx),
                              parser.level(idx),
                              parser.profile(idx))
                ctn.add_stream(v, idx)

            elif parser.codec_type(idx) == 'audio':
                a = AudioStream(parser.codec(idx))
                a.add_options(parser.channels(idx),
                              parser.language(idx),
                              parser.bitrate(idx),
                              parser.disposition(idx))
                ctn.add_stream(a, idx)

            elif parser.codec_type(idx) == 'subtitle':
                s = SubtitleStream(parser.codec(idx))
                s.add_options(parser.language(idx),
                              parser.disposition(idx))
                ctn.add_stream(s, idx)

        return ctn
