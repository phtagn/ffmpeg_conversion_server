# coding=utf-8
"""
This module contains the logic to build targetcontainers with the appropriate streams from a sourcecontainer
"""
from abc import ABCMeta, abstractmethod
from converter.streams import AudioStream, VideoStream, SubtitleStream, Container
from converter.source import SourceVideoStream, SourceAudioStream, SourceSubtitleStream
from converter.streamtemplates import TemplateFactory, VideoStreamTemplate, AudioStreamTemplate, SubtitleStreamTemplate

import logging
log = logging.getLogger(__name__)

# TODO: build bad codecs logic. There are some codecs that we cannot transcode from.
badtranscodecodecs = []


class TargetContainer(Container):

    def __init__(self, format):
        super(TargetContainer, self).__init__(format)

    def add_stream(self, stream) -> bool:
        assert isinstance(stream, (TargetVideoStream,TargetAudioStream, TargetSubtitleStream))

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

    def __init__(self, codec, channels, bitrate, language, sourceindex, willtranscode):
        super(TargetAudioStream, self).__init__(codec, channels, bitrate, language)
        self.sourceindex = sourceindex
        self.willtranscode = willtranscode


class TargetVideoStream(VideoStream):

    def __init__(self, codec: str, pix_fmt: str, bitrate: int, height: int, width: int, profile: str, level: float, sourceindex: int, willtranscode: bool, src_height: int, src_width: int):
        super(TargetVideoStream, self).__init__(codec, pix_fmt, bitrate, height, width, profile, level)
        self.sourceindex = sourceindex
        self.willtranscode = willtranscode
        self.src_width = src_width
        self.src_height = src_height


class TargetSubtitleStream(SubtitleStream):

    def __init__(self, codec, language, sourceindex, willtranscode):
        super(TargetSubtitleStream, self).__init__(codec, language)
        self.sourceindex = sourceindex
        self.willtranscode = willtranscode


class TargetContainerFactory(object):
    """Build a TargetContainer object with the proper streams"""

    def __init__(self, config, typ):
        if typ in config['Containers']:
            cfg = config['Containers'][typ]

            self.type = typ

            self.video_accepted_formats = cfg['video'].get('accepted_track_formats')
            self.video_prefer_method = cfg['video'].get('prefer_method')
            self.video_transcode_to = cfg['video'].get('transcode_to')

            self.audio_accepted_formats = cfg['audio'].get('accepted_track_formats')
            self.audio_transcode_to = cfg['audio'].get('transcode_to')
            self.audio_force_create = cfg['audio'].get('force_create_tracks')
            self.audio_copy_original = cfg['audio'].get('audio_copy_original')

            self.subtitle_accepted_formats = cfg['subtitle'].get('accepted_track_formats')


            self.audio_accepted_languages = config['Languages'].get('audio')
            self.subtitle_accepted_languages = config['Languages'].get('subtitle')
            self.subtitle_transcode_to = cfg['subtitle'].get('transcode_to')
            self.config = config

        else:
            raise Exception('Unsupported container type')

    def build_target_container(self, sourcecontainer) -> TargetContainer:
        """Builds a target container from the sourcecontainer and the options provided by the user.
        It takes all of the stream types in order of video, audio and subtitle, and generates a TargetContainer
        that conforms with the options"""

        assert isinstance(sourcecontainer, Container)
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

        subtitlestreams = filterlanguages(sourcecontainer.subtitlestreams, self.subtitle_accepted_languages, relax=False)
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
    def copystream(stream):
        """Copies the sourcestream into a targetstream"""
        pass

    @staticmethod
    @abstractmethod
    def conformtotemplate(stream, template):
        """Takes a template and sets the options of the"""
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
                                 sourceindex=stream.index,
                                 willtranscode=False,
                                 src_height=stream.height,
                                 src_width=stream.width)

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
                                     sourceindex=stream.index,
                                     willtranscode=True,
                                     src_width=stream.width,
                                     src_height=stream.height)

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
                                     sourceindex=stream.index,
                                     willtranscode=willtranscode,
                                     src_height=stream.height,
                                     src_width=stream.width)


class AudioStreamGenerator(IStreamGenerator):

    @staticmethod
    def copystream(stream) -> TargetAudioStream:
        assert isinstance(stream, SourceAudioStream)
        return TargetAudioStream(codec=stream.codec,
                                 channels=stream.channels,
                                 bitrate=stream.bitrate,
                                 language=stream.language,
                                 sourceindex=stream.index,
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
                                     sourceindex=stream.index,
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
                                 sourceindex=stream.index,
                                 willtranscode=willtranscode)


class SubtitleStreamGenerator(IStreamGenerator):
    @staticmethod
    def copystream(stream) -> TargetSubtitleStream:
        assert isinstance(stream, SourceSubtitleStream)
        return TargetSubtitleStream(codec=stream.codec,
                                    language=stream.language,
                                    sourceindex=stream.index,
                                    willtranscode=False)

    @staticmethod
    def conformtotemplate(stream, template):
        assert isinstance(stream, SourceSubtitleStream)
        assert isinstance(template, SubtitleStreamTemplate)

        if stream.codec != template.codec:
            return TargetSubtitleStream(codec=template.codec,
                                        language=stream.language,
                                        sourceindex=stream.index,
                                        willtranscode=True)
        else:
            return TargetSubtitleStream(codec=stream.codec,
                                        language=stream.language,
                                        sourceindex=stream.index,
                                        willtranscode=False)




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


