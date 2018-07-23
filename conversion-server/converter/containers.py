from typing import Union, Optional
from converter.streams import AudioStream, VideoStream, SubtitleStream
import logging

log = logging.getLogger(__name__)


class Container(object):
    """
    Container class representing a media file (e.g. avi, mp4, mkv...). A source_container has streams which themselves
    have options. At the moment containers support 3 types of streams, namely video, audio and subtitle.
    """
    supported_formats = ['mp4', 'matroska']

    def __init__(self, fmt, file_path=None):
        """

        :param fmt: the format of the source_container, as ffmpeg describes it.
        :type fmt: str
        """
        if fmt in self.supported_formats:
            self.format = fmt
            self.streams = {}
            self.audio_streams = {}
            self.video_streams = {}
            self.subtitle_streams = {}
            self.file_path = file_path
        else:
            raise Exception('Format %s not supported', fmt)

    def add_stream(self, stream: Union[AudioStream, VideoStream, SubtitleStream],
                   stream_number: Optional[int] = None, duplicate_check=False) -> int:
        """
        Adds a stream to the source_container. The stream has to be of a supported type.
        :param stream: The stream to add.
        :type stream: AudioStream, VideoStream or SubtitleStream
        :param stream_number: 0-based number of the stream, in *absolute* terms (i.e. not relative to its type).
        If not supplied, the method will compute the next available stream number.
        :type stream_number: int
        :param duplicate_check: Indicates whether the source_container should check that streams are not duplicated.
        See is_duplicate.
        :type duplicate_check: bool
        :return: Number of the stream that was added, None if the stream was rejected
        :rtype: int or None
        """
        assert isinstance(stream, (VideoStream, AudioStream, SubtitleStream))
        if not duplicate_check or not self.is_duplicate(stream):
            if stream_number is not None:
                sn = stream_number
            else:
                sn = len(self.streams)
            if stream_number in self.streams.keys():
                log.info('Replacing stream %s', stream_number)

            self.streams.update({sn: stream})

            if isinstance(stream, VideoStream):
                self.video_streams.update({stream: len(self.video_streams)})
            elif isinstance(stream, AudioStream):
                self.audio_streams.update({stream: len(self.audio_streams)})
            elif isinstance(stream, SubtitleStream):
                self.subtitle_streams.update({stream: len(self.subtitle_streams)})

            return sn

    def relative_stream_number(self, stream):
        try:
            return self.video_streams[stream]
        except KeyError:
            pass
        try:
            return self.audio_streams[stream]
        except KeyError:
            pass
        try:
            return self.subtitle_streams[stream]
        except KeyError:
            return None

    def absolute_stream_number(self, stream):
        for k, v in self.streams.values():
            if v == stream:
                return k
        return None

    def is_duplicate(self, stream):
        """
        Checks whether a stream is a duplicate of an existing stream already present in the source_container. See __eq__ method
        of Streams class to see how duplicate checking occurs.
        :param stream: Stream to be checked against the source_container
        :type stream: AudioStream, VideoStream or SubtitleStream
        :return: True or False
        :rtype: bool
        """

        if isinstance(stream, AudioStream):
            for k in self.audio_streams:
                if stream == k:
                    return True
        if isinstance(stream, VideoStream):
            for k in self.video_streams:
                if stream.codec == self.video_streams[k].codec and stream == self.video_streams[k]:
                    return True
        if isinstance(stream, SubtitleStream):
            for k in self.subtitle_streams:
                if stream.codec == self.subtitle_streams[k].codec and stream == self.subtitle_streams[k]:
                    return True

        return False


class ContainerFactory(object):
    """Factory class to build a source_container"""
    @staticmethod
    def container_from_ffprobe(filepath, ffmpeg) -> Container:
        """
        Builds a source_container from the output of ffprobe. A parser object from the parsers.py
        :param filepath: path of the file to analyse
        :type filepath: os.path
        :param ffmpeg: an initialised ffmpeg object
        :type ffmpeg: converter.ffmpeg.FFmpeg
        :return: a source_container filled with streams
        :rtype: Container
        """
        parser = ffmpeg.probe(filepath)

        if 'matroska' in parser.format:
            ctn = Container('matroska', filepath)
        elif 'mp4' in parser.format:
            ctn = Container('mp4', filepath)
        else:
            ctn = Container(parser.format, filepath)

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
