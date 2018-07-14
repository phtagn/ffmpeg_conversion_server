from typing import Union, Optional
from converter.streams import AudioStream, VideoStream, SubtitleStream
import logging

log = logging.getLogger(__name__)


class Container(object):
    supported_formats = ['mp4', 'matroska']

    def __init__(self, fmt):
        if fmt in self.supported_formats:
            self.format = fmt
            self.streams = {}
            self.audio_streams = {}
            self.video_streams = {}
            self.subtitle_streams = {}

        else:
            raise Exception('Format %s not supported', fmt)

    def add_stream(self, stream: Union[AudioStream, VideoStream, SubtitleStream],
                   stream_number: Optional[int] = None, duplicate_check=False) -> int:

        assert isinstance(stream, (VideoStream, AudioStream, SubtitleStream))
        if not duplicate_check or not self.is_duplicate(stream):
            if stream_number is not None:
                sn = stream_number
            else:
                sn = len(self.streams)
                # sn += 1 if sn > 0 else 0
            if stream_number in self.streams.keys():
                log.info('Replacing stream %s', stream_number)

            self.streams.update({sn: stream})

            if isinstance(stream, VideoStream):
                self.video_streams.update({sn: stream})
            elif isinstance(stream, AudioStream):
                self.audio_streams.update({sn: stream})
            elif isinstance(stream, SubtitleStream):
                self.subtitle_streams.update({sn: stream})

            return sn

    def is_duplicate(self, stream):
        if isinstance(stream, AudioStream):
            for k in self.audio_streams:
                if stream.codec == self.audio_streams[k].codec and stream == self.audio_streams[k]:
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

    @staticmethod
    def container_from_ffprobe(filepath, ffmpeg) -> Container:

        parser = ffmpeg.probe(filepath)

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
