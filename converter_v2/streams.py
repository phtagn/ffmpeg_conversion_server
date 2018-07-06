from converter_v2.encoders import *
from converter_v2.optionbuilder import OptionBuilder
from converter_v2.streamoptions import *
import logging
import copy

log = logging.getLogger(__name__)


class Stream(ABC):
    """
    Generic stream class, it is not to be instantiated directly. Use concrete classes VideoStream, AudioStream and SubtitleStream
    """
    supported_options = []
    multiple = []

    def __init__(self, allow_multiple=False):
        self._options = Options(allow_multiple=allow_multiple)

    def add_option(self, *options):
        """Add options to the options pool. Reject options if they are not supported or if the value is None.
        """
        for opt in options:
            if type(opt) in self.supported_options:
                self._options.add_options(opt)

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
        for _, opt in self.options:
            newopt = copy.copy(opt)
            new.add_option(newopt)
        return new

    def __str__(self):
        output = {name: opt.value for name, opt in self.options}
        return str(output)

    def __hash__(self):
        return hash(str(self))


class StreamFactory(object):

    @classmethod
    def get_stream_by_type(cls, stream: Stream) -> Stream:
        assert isinstance(stream, (VideoStream, AudioStream, SubtitleStream))
        if isinstance(stream, VideoStream):
            return VideoStream()
        elif isinstance(stream, AudioStream):
            return AudioStream()
        elif isinstance(stream, SubtitleStream):
            return SubtitleStream()


class VideoStream(Stream):
    supported_options = [Codec, PixFmt, Bitrate, Disposition, Height, Width, Level, Profile]


class AudioStream(Stream):
    supported_options = [Codec, Channels, Language, Disposition, Bitrate]


class SubtitleStream(Stream):
    supported_options = [Codec, Language, Disposition]


class Streams(object):
    """A collection object for streams. Handles sorting them in their different categories"""

    def __init__(self, allow_identical=False):
        self._audio_streams = []
        self._video_streams = []
        self._subtitle_streams = []
        self.allow_identical = allow_identical

    def add_stream(self, stream: Union[VideoStream, AudioStream, SubtitleStream]):
        if isinstance(stream, VideoStream):
            self._video_streams.append(stream)
        elif isinstance(stream, AudioStream):
            self._audio_streams.append(stream)
        elif isinstance(stream, SubtitleStream):
            self._subtitle_streams.append(stream)
        else:
            raise TypeError('Streams can only be one of VideoStream, AudioStream and SubtitleStream')

    @property
    def video(self):
        return self._video_streams

    @property
    def audio(self):
        return self._audio_streams

    @property
    def subtitle(self):
        return self._subtitle_streams

    @property
    def streams(self):
        return [*self._video_streams, *self._audio_streams, *self._subtitle_streams]

    def __iter__(self):
        for s in self.streams:
            yield s

    def __len__(self):
        return len(self.streams)

    def __eq__(self, other):
        if not isinstance(other, Streams):
            return False

        if (Counter(self.video) == Counter(other.video) and
                Counter(self.audio) == Counter(other.audio) and
                Counter(self.subtitle) == Counter(other.subtitle)):
            return True

        return False



if __name__ == '__main__':


    s1 = Streams()
    s2 = Streams()

    v1 = VideoStream()
    v2 = VideoStream()
    v3 = VideoStream()
    v4 = AudioStream()

    v1.add_option(Codec('h264'), Bitrate(512))
    v2.add_option(Bitrate(512), Codec('h264'))

    v3.add_option(Codec('h264'), Bitrate(512))
    v4.add_option(Bitrate(512), Codec('h264'))
    print(v1==v2)

    s1.add_stream(v1)
    s1.add_stream(v2)

    s2.add_stream(v4)
    s2.add_stream(v3)

    for k in s1.video:
        print(k)
    print(s1 == s2)