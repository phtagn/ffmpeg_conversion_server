from abc import ABC
from converter_v2.streamoptions import *
import logging
import copy

log = logging.getLogger(__name__)


class Stream(ABC):
    """
    Generic stream class, it is not to be instantiated directly. Use concrete classes VideoStream, AudioStream and
    SubtitleStream
    """
    supported_options = []
    multiple = []

    def __init__(self, codec: Codec):
        assert isinstance(codec, Codec)
        self._options = Options()
        self.codec = codec

    def add_options(self, *_options):
        """Add options to the options pool. Reject options if they are not supported.
        """
        for _opt in _options:
            if type(_opt) in self.supported_options and _opt.value is not None:
                self._options.add_option(_opt)
            else:
                log.warning('Option %s was rejected because unsupported by %s', str(_opt),
                            self.__class__.__name__)

    @property
    def options(self):
        return self._options

    def __eq__(self, other):
        """Compares streams by comparing the value of options
        attached to them. IMPORTANT: If the option is missing in other, a match will be
        assumed and the comparison will return True. This is a design decision
        so that when building streams from templates, you don't have to specify every single option
        present in a source stream built from a ffprobe."""

        if not isinstance(other, type(self)):
            return False
        return self.options == other.options

    def __copy__(self):
        new = type(self)()
        for _opt in self.options:
            newopt = copy.copy(_opt)
            new.options.add_option(newopt)
        return new

    def __str__(self):
        output = {_opt.__class.__name: _opt.value for _opt in self.options}
        return str(output)

    def __hash__(self):
        return hash(self.options)


class VideoStream(Stream):
    supported_options = [Codec, PixFmt, Bitrate, Disposition, Height, Width, Level, Profile]
    kind = 'video'


class AudioStream(Stream):
    supported_options = [Codec, Channels, Language, Disposition, Bitrate]
    kind = 'audio'


class SubtitleStream(Stream):
    supported_options = [Codec, Language, Disposition]
    kind = 'subtitle'


class StreamFactory(object):

    @classmethod
    def get_stream_by_type(cls, stream: Stream, codec) -> Stream:
        assert isinstance(stream, (VideoStream, AudioStream, SubtitleStream))
        if isinstance(stream, VideoStream):
            return VideoStream(codec)
        elif isinstance(stream, AudioStream):
            return AudioStream(codec)
        elif isinstance(stream, SubtitleStream):
            return SubtitleStream(codec)

    @classmethod
    def get_stream_by_name(cls, name, codec) -> Stream:
        assert name in ['audio', 'video', 'subtitle']
        if name == 'video':
            return VideoStream(codec)
        elif name == 'audio':
            return AudioStream(codec)
        elif name == 'subtitle':
            return SubtitleStream(codec)
