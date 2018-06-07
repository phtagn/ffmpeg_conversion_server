"""
This module holds the representation of the input and output.
The main input is a container of type ContainerInfo, which itself contains video, audio and subtitle streams.
The container format should be indicated. At the moment the container format should be expressed to be undertandable
by ffmpeg. For example, mkv files should be called 'matroska'.
Every class (ContainerInfo, VideoStreamInfo, AudioStreamInfo, and SubtitleStreamInfo has a child class that starts with
Target.
The child class can be compared to the parent class which all implement __eq__ and __ne__
The child class contains supplemental such as sourceindex and willtranscode which respectively indicate the index of the
source stream and whether getting from the source stream to the targetstream will necessitate transcoding.
"""
from typing import Union

class Container(object):

    def __init__(self, format):
        self._videostreams = []
        self._audiostreams = []
        self._subtitlestreams = []
        self._format = format


    @property
    def videostreams(self):
        return self._videostreams

    @videostreams.setter
    def videostreams(self, vsi):
        self._videostreams.append(vsi)

    @property
    def audiostreams(self):
        return self._audiostreams

    @audiostreams.setter
    def audiostreams(self, asi):
        self._audiostreams.append(asi)

    @property
    def subtitlestreams(self):
        return self._subtitlestreams

    @subtitlestreams.setter
    def subtitlestreams(self, ssi):
        self._subtitlestreams.append(ssi)

    def add_stream(self, stream):
        assert isinstance(stream, (VideoStream, AudioStream, SubtitleStream))

        if stream.type == 'video':
            streams = self.videostreams
        elif stream.type == 'audio':
            streams = self.audiostreams
        elif stream.type == 'subtitle':
            streams = self.subtitlestreams
        else:
            raise Exception(f'{stream.type} not one of audio, video, subtitle')

        # Avoid adding multiple identical streams for TargetStreams
        try:
            idx = streams.index(stream)
            if isinstance(stream, (TargetVideoStream, TargetAudioStream, TargetSubtitleStream)) and isinstance(self, TargetContainer):
                if stream.willtranscode is True and streams[idx].willtranscode is False:
                    streams.pop(idx)
                    streams.append(stream)
        except ValueError:
            streams.append(stream)

    @property
    def format(self):
        return 'matroska'


class TargetContainer(Container):

    def get_streams_from_source_index(self, typ: str, index: int):
        if typ not in ['video', 'audio', 'subtitle']:
            raise Exception(f'Type f{typ} is not one of video, audio or subtitle')

        if typ == 'video':
            return [stream for stream in self.videostreams if stream.sourceindex == index]

        elif typ == 'audio':
            return [stream for stream in self.audiostreams if stream.sourceindex == index]

        elif typ == 'subtitle':
            return [stream for stream in self.subtitlestreams if stream.sourceindex == index]
        

    def getvideofromsource(self, index):
        return self.get_streams_from_source_index('video', index)

    def getaudiofromsource(self, index):
        return self.get_streams_from_source_index('audio', index)


    def getsubtitlefromsource(self, index):
        return self.get_streams_from_source_index('subtitle', index)


    def getaudiotranscode(self):
        return [stream for stream in self.audiostreams if stream.willtranscode]

    def audioNotTranscode(self):
        return [stream for stream in self.audiostreams if not stream.willtranscode]

class ContainerFactory(object):
    """Factory class to return an instance of ContainerInfo"""
    @staticmethod
    def fromparser(parser):
        """
        Instantiates and returns a container of type ContainerInfo with all of the streams from a parser.
        :param parser: a parser that conforms to the IParser interface
        :return: ContainerInfo
        """
        container = Container(parser.format)

        for stream in parser.streams:
            if stream['codec_type'] == 'video':
                index = stream['index']
                s = SourceVideoStream(index=index,
                                    codec=parser.codec(index),
                                    pix_fmt=parser.pix_fmt(index),
                                    bitrate=parser.bitrate(index),
                                    height=parser.height(index),
                                    width=parser.width(index),
                                    profile=parser.profile(index),
                                    level=parser.level(index))

                container.add_stream(s)

            if stream['codec_type'] == 'audio':
                index = stream['index']
                s = SourceAudioStream(index=index,
                                    channels=parser.channels(index),
                                    language=parser.language(index),
                                    codec=parser.codec(index),
                                    bitrate=parser.bitrate(index))

                container.add_stream(s)

            if stream['codec_type'] == 'subtitle':
                index = stream['index']
                s = SourceSubtitleStream(index=index,
                                       codec=parser.codec(index),
                                       language=parser.language(index))

                container.add_stream(s)

        return container


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

    def __init__(self, index, codec, language):
        self.index = index
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


class SourceVideoStream(VideoStream):

    def __init__(self,
                 index,
                 codec,
                 pix_fmt,
                 bitrate,
                 height,
                 width,
                 profile,
                 level):

        super(SourceVideoStream, self).__init__(codec, pix_fmt, bitrate, height, width, profile, level)
        self.index = index


class SourceAudioStream(AudioStream):

    def __init__(self, index, codec, channels, bitrate, language):

        super(SourceAudioStream, self).__init__(codec, channels, bitrate, language)
        self.index = index


class SourceSubtitleStream(SubtitleStream):

    def __init__(self, index, codec, language):
        self.index = index
        super(SourceSubtitleStream, self).__init__(codec, language)


class TargetAudioStream(AudioStream):

    def __init__(self, codec, channels, bitrate, language, sourceindex, willtranscode):
        super(TargetAudioStream, self).__init__(codec, channels, bitrate, language)
        self.sourceindex = sourceindex
        self.willtranscode = willtranscode


class TargetVideoStream(VideoStream):

    def __init__(self, codec: str, pix_fmt: str, bitrate: int, height: int, width: int, profile: str, level: float, sourceindex: int, willtranscode: bool):
        super(TargetVideoStream, self).__init__(codec, pix_fmt, bitrate, height, width, profile, level)
        self.sourceindex = sourceindex
        self.willtranscode = willtranscode


class TargetSubtitleStream(SubtitleStream):

    def __init__(self, codec, language, sourceindex, willtranscode):
        super(TargetSubtitleStream, self).__init__(codec, language)
        self.sourceindex = sourceindex
        self.willtranscode = willtranscode