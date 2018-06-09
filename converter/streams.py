from typing import Union, List

from converter.formats import FormatFactory



class Stream(object):
    pass


class VideoStream(Stream):
    def __init__(self,
                 codec,
                 pix_fmt,
                 bitrate,
                 height,
                 width,
                 profile,
                 level):

        self.codec = codec
        self.pix_fmt = pix_fmt
        self.bitrate = bitrate
        self.height = height
        self.width = width
        self.profile = profile
        self.level = level
        self.type = 'video'

    def __eq__(self, other):
        if not isinstance(other, VideoStream):
            return False

        if (self.codec == other.codec and
            self.pix_fmt == other.pix_fmt and
            self.bitrate == other.bitrate and
            self.height == other.height and
            self.width == other.width and
            self.profile == other.profile and
            self.level == other.level):
            return True

        return False

    def __ne__(self, other):
        if not isinstance(other, VideoStream):
            return True

        if (self.codec != other.codec or
            self.pix_fmt != other.pix_fmt or
            self.bitrate != other.bitrate or
            self.height != other.height or
            self.width != other.width or
            self.profile != other.profile or
            self.level != other.level):
            return True

        return False


class AudioStream(Stream):

    def __init__(self, codec, channels, bitrate, language):
        self.language = language
        self.channels = channels
        self.bitrate = bitrate
        self.codec = codec
        self.type = 'audio'

    def __eq__(self, other):
        if not isinstance(other, AudioStream):
            return False

        if (self.codec == other.codec and
                self.language == other.language and
                self.channels == other.channels and
                self.bitrate == other.bitrate):
            return True

        return False

    def __ne__(self, other):
        if not isinstance(other, AudioStream):
            return True

        if (self.codec != other.codec or
                self.language != other.language or
                self.channels != other.channels or
                self.bitrate != other.bitrate):
            return True

        return False


class SubtitleStream(Stream):

    def __init__(self, codec, language):
        self.codec = codec
        self.language = language
        self.type = 'subtitle'

    def __eq__(self, other):
        if not isinstance(other, SubtitleStream):
            return False

        if (self.codec == other.codec and
            self.language == other.language):
            return True

        return False


class Container(object):

    def __init__(self, format):
        self._videostreams = []
        self._audiostreams = []
        self._subtitlestreams = []
        self._format = format

    @property
    def videostreams(self):
        return self._videostreams

    @property
    def audiostreams(self):
        return self._audiostreams

    @property
    def subtitlestreams(self):
        return self._subtitlestreams

    @property
    def streams(self):
        return [stream for streamlist in [self.videostreams, self.audiostreams, self.subtitlestreams] for stream in
                streamlist]

    def add_stream(self, stream):
        pass


    @property
    def format(self):
        return FormatFactory.get_format(self._format)

    def get_streams_from_property(self, typ: str, **kwargs) -> List[Union[VideoStream, AudioStream, SubtitleStream]]:
        if typ not in ['video', 'audio', 'subtitle']:
            raise Exception(f'Type f{typ} is not one of video, audio or subtitle')
        s = []

        if len(kwargs) > 1:
            raise Exception('Only 1 criterion is allowed')

        k, v = list(kwargs.items())[0]

        if typ == 'video':
            streams = self.videostreams
        elif typ == 'audio':
            streams = self.audiostreams
        elif typ == 'subtitle':
            streams = self.subtitlestreams

        for stream in streams:
            if hasattr(stream, k) and getattr(stream, k) == v:
                s.append(stream)

        return s
