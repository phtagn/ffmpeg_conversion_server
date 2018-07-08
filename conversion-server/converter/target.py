# coding=utf-8
"""
converter.target
________________

This module contains the logic to build targetcontainers with the appropriate streams from a source container.
Target containers are built by comparing source containers with a set of options. The resulting target containers
contain streams (audio, video and subtitle streams). The target containers can then be used to determine which
codec are needed to create the track contained in the target container from the tracks in the source container.
"""
from abc import ABCMeta, abstractmethod
from converter.streams import AudioStream, VideoStream, SubtitleStream, Container, Stream
from converter.source import SourceVideoStream, SourceAudioStream, SourceSubtitleStream, SourceContainer
from converter.streamtemplates import TemplateFactory, VideoStreamTemplate, AudioStreamTemplate, SubtitleStreamTemplate
from typing import Union

import logging

log = logging.getLogger(__name__)

# TODO: build bad codecs logic. There are some codecs that we cannot transcode from.
badtranscodecodecs = []


class TargetContainer(Container):

    def __init__(self, format):
        super(TargetContainer, self).__init__(format)

    def add_stream(self, stream) -> bool:
        assert isinstance(stream, (TargetVideoStream, TargetAudioStream, TargetSubtitleStream))

        if stream.type == 'video':
            streams = self.videostreams
        elif stream.type == 'audio':
            streams = self.audiostreams
        elif stream.type == 'subtitle':
            streams = self.subtitlestreams
        else:
            raise Exception(f'{stream.type} not one of audio, video, subtitle')

        # Do not add streams if not supported by container
        if self.format.supports(stream.codec, stream.type):
            # Avoid adding multiple identical streams for TargetStreams
            try:
                idx = streams.index(stream)
                if stream.willtranscode is True and streams[idx].willtranscode is False:
                    streams.pop(idx)
                    streams.append(stream)
            except ValueError:
                streams.append(stream)


class TargetAudioStream(AudioStream):

    def __init__(self, sourcestream, willtranscode, *args, **kwargs):
        super(TargetAudioStream, self).__init__(*args, **kwargs)
        self.sourcestream = sourcestream
        self.willtranscode = willtranscode


class TargetVideoStream(VideoStream):

    def __init__(self, sourcestream, willtranscode: bool, *args, **kwargs):
        super(TargetVideoStream, self).__init__(*args, **kwargs)
        self.sourcestream = sourcestream
        self.willtranscode = willtranscode


class TargetSubtitleStream(SubtitleStream):

    def __init__(self, sourcestream, willtranscode, *args, **kwargs):
        super(TargetSubtitleStream, self).__init__(*args, **kwargs)
        self.sourcestream = sourcestream
        self.willtranscode = willtranscode


class TargetContainerFactory(object):
    """Build a TargetContainer object with the proper streams"""

    def __init__(self, config,
                 video_accepted_formats: list,
                 video_prefer_method: str,
                 video_transcode_to: str,
                 audio_accepted_formats: list,
                 audio_transcode_to: str,
                 audio_force_create: list,
                 audio_copy_original: bool,
                 audio_accepted_languages: list,
                 subtitle_accepted_formats: list,
                 subtitle_accepted_languages: list,
                 subtitle_transcode_to: str,
                 typ):
        """

        :param config:
        :param video_accepted_formats: list of accepted stream formats e.g. [h264, hevc]
        :param video_prefer_method: str, one of 'copy', 'transcode', 'override', indicates the preferred method for
        processing an input stream
        :param video_transcode_to: str, one of the available video stream formats (see the streamformats module)
        :param audio_accepted_formats:
        :param audio_transcode_to: str, one of the available audio stream formats (see the streamformats module)
        :param audio_force_create: list of available stream formats
        :param audio_copy_original: bool, if true will always copy the original tracks and create new tracks based on
        force create
        :param audio_accepted_languages:
        :param subtitle_accepted_formats:
        :param subtitle_accepted_languages:
        :param subtitle_transcode_to:
        :param typ: str, one of the available container formats.
        """


        if typ in config['Containers']:

            self.type = typ

            self.video_accepted_formats = video_accepted_formats
            self.video_prefer_method = video_prefer_method
            self.video_transcode_to = video_transcode_to

            self.audio_accepted_formats = audio_accepted_formats
            self.audio_transcode_to = audio_transcode_to
            self.audio_force_create = audio_force_create
            self.audio_copy_original = audio_copy_original

            self.subtitle_accepted_formats = subtitle_accepted_formats

            self.audio_accepted_languages = audio_accepted_languages
            self.subtitle_accepted_languages = subtitle_accepted_languages
            self.subtitle_transcode_to = subtitle_transcode_to

            self.config = config

        else:
            raise Exception('Unsupported container type')

    def build_target_container(self, sourcecontainer: SourceContainer) -> TargetContainer:
        """Builds a target container from the sourcecontainer and the options provided by the user.
        It takes all of the stream types in order of video, audio and subtitle, and generates a TargetContainer
        that conforms with the options"""

        assert isinstance(sourcecontainer, SourceContainer)
        ctn = TargetContainer(self.type)

        for stream in sourcecontainer.videostreams:
            template = TemplateFactory.get_template(self.config, stream.type, stream.codec)
            if stream.codec in self.video_accepted_formats and self.video_prefer_method == 'copy':
                s = StreamGeneratorFactory.copystream(stream)

            elif stream.codec in self.video_prefer_method and self.video_prefer_method == 'override':
                s = StreamGeneratorFactory.conformtotemplate(stream, template)

            else:
                template = TemplateFactory.get_template(self.config, stream.type, self.video_transcode_to)
                s = StreamGeneratorFactory.conformtotemplate(stream, template)

            ctn.add_stream(s)

        audiostreams = filterlanguages(sourcecontainer.audiostreams, self.audio_accepted_languages, relax=True)
        for stream in audiostreams:
            if stream.codec in self.audio_accepted_formats:
                s = StreamGeneratorFactory.copystream(stream)
            else:
                template = TemplateFactory.get_template(self.config, stream.type, self.audio_transcode_to)
                s = StreamGeneratorFactory.conformtotemplate(stream, template)

            ctn.add_stream(s)

            for fmt in self.audio_force_create:
                template = TemplateFactory.get_template(self.config, stream.type, fmt)
                s = StreamGeneratorFactory.conformtotemplate(stream, template)
                ctn.add_stream(s)

            if self.audio_copy_original:
                s = StreamGeneratorFactory.copystream(stream)
                ctn.add_stream(s)

        subtitlestreams = filterlanguages(sourcecontainer.subtitlestreams, self.subtitle_accepted_languages,
                                          relax=False)
        for stream in subtitlestreams:
            if stream.codec in self.subtitle_accepted_formats:
                s = StreamGeneratorFactory.copystream(stream)
            else:
                template = TemplateFactory.get_template(self.config, stream.type, self.subtitle_transcode_to)
                s = StreamGeneratorFactory.conformtotemplate(stream, template)
            ctn.add_stream(s)

        return ctn


class IStreamGenerator(metaclass=ABCMeta):
    """Interface for stream generators. TargetStreams can be built in 2 different ways:
    1) The stream can be copied from a source stream. This does not involve a template.
    2) The stream can be checked against the template and its parameters adjusted accordingly
    In any case, we always need the source index to be able to map the targetstream to the source stream"""

    @staticmethod
    @abstractmethod
    def copystream(stream: Union[AudioStream, VideoStream, SubtitleStream]) -> Union[
        TargetVideoStream, TargetAudioStream, TargetSubtitleStream]:
        """Copies the sourcestream into a targetstream"""
        pass

    @staticmethod
    @abstractmethod
    def conformtotemplate(stream: Union[AudioStream, VideoStream, SubtitleStream],
                          template: Union[AudioStreamTemplate, VideoStreamTemplate, SubtitleStreamTemplate]) -> Union[
        TargetVideoStream, TargetAudioStream, TargetSubtitleStream]:
        """Takes a stream and a template and returns a TargetTemplate conforming with the template.
        For example, if the input stream has a bitrate of 1500k when only 1000k are allowed in the template
        returns a target stream with a bitrate of 1000k. Conversely, if stream.bitrate = 1200k and
        template.max_bitrate = 1500k, the target container will have a 1200k bitrate."""
        pass


class StreamGeneratorFactory(IStreamGenerator):
    """Simple factory that returns the appropriate StreamGenerator from the type of the input stream."""

    @staticmethod
    def copystream(stream):
        if stream.type == 'video':
            return VideoStreamGenerator.copystream(stream)
        elif stream.type == 'audio':
            return AudioStreamGenerator.copystream(stream)
        elif stream.type == 'subtitle':
            return SubtitleStreamGenerator.copystream(stream)

    @staticmethod
    def conformtotemplate(stream, template):
        if stream.type == 'video':
            return VideoStreamGenerator.conformtotemplate(stream, template)
        elif stream.type == 'audio':
            return AudioStreamGenerator.conformtotemplate(stream, template)
        elif stream.type == 'subtitle':
            return SubtitleStreamGenerator.conformtotemplate(stream, template)


class VideoStreamGenerator(IStreamGenerator):

    @staticmethod
    def copystream(stream) -> TargetVideoStream:
        assert isinstance(stream, SourceVideoStream)
        return TargetVideoStream(codec=stream.codec,
                                 pix_fmt=stream.pix_fmt,
                                 bitrate=stream.bitrate,
                                 height=stream.height,
                                 width=stream.width,
                                 profile=stream.profile,
                                 level=stream.level,
                                 sourcestream=stream,
                                 disposition=stream.disposition,
                                 willtranscode=False)

    @staticmethod
    def conformtotemplate(stream, template):
        assert isinstance(stream, SourceVideoStream)
        assert isinstance(template, VideoStreamTemplate)

        if stream.codec != template.codec:
            return TargetVideoStream(codec=template.codec,
                                     pix_fmt=template.pix_fmts[0] if template.pix_fmts else None,
                                     bitrate=template.max_bitrate if template.max_bitrate else None,
                                     height=template.max_height if template.max_height else stream.height,
                                     width=template.max_width if template.max_width else stream.width,
                                     profile=template.profiles[0] if template.profiles else None,
                                     level=template.max_level if template.max_level else None,
                                     sourcestream=stream,
                                     willtranscode=True)

        else:

            willtranscode = False
            if not template.pix_fmts or stream.pix_fmt in template.pix_fmts:
                pix_fmt = stream.pix_fmt
            else:
                pix_fmt = template.pix_fmts[0]
                willtranscode = True

            if not template.max_height or template.max_height > stream.height:
                height = stream.height
            else:
                height = template.max_height
                willtranscode = True

            if not template.max_width or template.max_width > stream.width:
                width = stream.width
            else:
                width = template.max_width
                willtranscode = True

            if template.max_bitrate and stream.bitrate and stream.bitrate > template.max_bitrate:
                bitrate = template.max_bitrate
                willtranscode = True
            else:
                bitrate = stream.bitrate

            if template.max_level and stream.level and stream.level > template.max_level:
                level = template.max_level
                willtranscode = True
            else:
                level = stream.level

            # TODO : check that profile works
            if template.profiles and stream.profile and stream.profile == template.profiles:
                profile = template.profiles[0]
                willtranscode = True
            else:
                profile = stream.profile

            return TargetVideoStream(codec=stream.codec,
                                     pix_fmt=pix_fmt,
                                     height=height,
                                     width=width,
                                     bitrate=bitrate,
                                     level=level,
                                     profile=profile,
                                     sourcestream=stream,
                                     willtranscode=willtranscode)


class AudioStreamGenerator(IStreamGenerator):

    @staticmethod
    def copystream(stream) -> TargetAudioStream:
        assert isinstance(stream, SourceAudioStream)
        return TargetAudioStream(codec=stream.codec,
                                 channels=stream.channels,
                                 bitrate=stream.bitrate,
                                 language=stream.language,
                                 sourcestream=stream,
                                 disposition=stream.disposition,
                                 willtranscode=False
                                 )

    @staticmethod
    def conformtotemplate(stream, template) -> TargetAudioStream:
        assert isinstance(stream, SourceAudioStream)
        assert isinstance(template, AudioStreamTemplate)

        if stream.codec != template.codec:
            return TargetAudioStream(codec=template.codec,
                                     bitrate=template.max_bitrate if template.max_bitrate else None,
                                     channels=template.max_channels if template.max_channels else None,
                                     language=stream.language,
                                     sourcestream=stream,
                                     disposition={},
                                     willtranscode=True)
        willtranscode = False

        if not template.max_bitrate and stream.bitrate and stream.bitrate > template.max_bitrate:
            bitrate = template.max_bitrate
            willtranscode = True
        else:
            bitrate = stream.bitrate

        if not template.max_channels or stream.channels > template.max_channels:
            channels = stream.channels
        else:
            channels = template.max_channels
            willtranscode = True

        return TargetAudioStream(codec=stream.codec,
                                 bitrate=bitrate,
                                 channels=channels,
                                 language=stream.language,
                                 sourcestream=stream,
                                 disposition={},
                                 willtranscode=willtranscode)


class SubtitleStreamGenerator(IStreamGenerator):
    @staticmethod
    def copystream(stream) -> TargetSubtitleStream:
        assert isinstance(stream, SourceSubtitleStream)
        return TargetSubtitleStream(codec=stream.codec,
                                    language=stream.language,
                                    sourcestream=stream,
                                    disposition=stream.disposition,
                                    willtranscode=False)

    @staticmethod
    def conformtotemplate(stream, template):
        assert isinstance(stream, SourceSubtitleStream)
        assert isinstance(template, SubtitleStreamTemplate)

        if stream.codec != template.codec:
            return TargetSubtitleStream(codec=template.codec,
                                        language=stream.language,
                                        sourcestream=stream,
                                        willtranscode=True,
                                        disposition={})
        else:
            return TargetSubtitleStream(codec=stream.codec,
                                        language=stream.language,
                                        sourcestream=stream,
                                        willtranscode=False,
                                        disposition={})


def filterlanguages(streamlist, languagelist, relax=False):
    """Helper function to select tracks based on language.
    If relax is True, then if the selection is empty, the function will
    return the original list of streams"""
    validstreams = []
    for stream in streamlist:
        if stream.language in languagelist:
            validstreams.append(stream)

    if not validstreams and relax is True:
        return streamlist
    else:
        return validstreams


class MissingFormatError(Exception):
    pass
