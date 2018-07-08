from converter.streams import VideoStream, AudioStream, SubtitleStream, Container
from typing import Type
from parsers.parsers import IParser


class SourceContainer(Container):

    def __init__(self, format):
        super(SourceContainer, self).__init__(format)

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

        streams.append(stream)


class SourceVideoStream(VideoStream):

    def __init__(self, index, *args, **kwargs):
        super(SourceVideoStream, self).__init__(*args, **kwargs)
        self.index = index


class SourceAudioStream(AudioStream):

    def __init__(self, index, *args, **kwargs):
        super(SourceAudioStream, self).__init__(*args, **kwargs)
        self.index = index


class SourceSubtitleStream(SubtitleStream):

    def __init__(self, index, *args, **kwargs):
        self.index = index
        super(SourceSubtitleStream, self).__init__(*args, **kwargs)


class SourceContainerFactory(object):
    """Factory class to return an instance of ContainerInfo"""

    @staticmethod
    def fromparser(parser: IParser) -> SourceContainer:
        """
        Instantiates and returns a container of type ContainerInfo with all of the streams from a parser.
        :param parser: a parser that conforms to the IParser interface
        :return: Container
        """
        container = SourceContainer(parser.format)

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
                                      level=parser.level(index),
                                      disposition=parser.disposition(index))

                container.add_stream(s)

            if stream['codec_type'] == 'audio':
                index = stream['index']
                s = SourceAudioStream(index=index,
                                      channels=parser.channels(index),
                                      language=parser.language(index),
                                      codec=parser.codec(index),
                                      bitrate=parser.bitrate(index),
                                      disposition=parser.disposition(index))

                container.add_stream(s)

            if stream['codec_type'] == 'subtitle':
                index = stream['index']
                s = SourceSubtitleStream(index=index,
                                         codec=parser.codec(index),
                                         language=parser.language(index),
                                         disposition=parser.disposition(index))

                container.add_stream(s)

        return container
