# coding=utf-8
from info.streaminfo import Container, SourceVideoStream, SourceAudioStream, SourceSubtitleStream, TargetAudioStream, \
    TargetVideoStream, TargetSubtitleStream, TargetContainer

import logging
from abc import ABCMeta, abstractmethod
log = logging.getLogger(__name__)

class TemplateFactory(object):
    """Returns a template object instantiated with the options from the config file"""
    @staticmethod
    def get_template(cfg, typ, trackformat):

        if trackformat in cfg['TrackFormats']:
            fmt = cfg['TrackFormats'][trackformat]
            if typ == 'video':
                return VideoStreamTemplate(codec=trackformat,
                                           pix_fmts=fmt.get('pix_fmts'),
                                           max_bitrate=fmt.get('max_bitrate'),
                                           max_height=fmt.get('max_height'),
                                           max_width=fmt.get('max_width'),
                                           profiles=fmt.get('profiles'),
                                           max_level=fmt.get('max_level'))
            elif typ == 'audio':
                return AudioStreamTemplate(codec=trackformat,
                                           max_channels=fmt.get('max_channels'),
                                           max_bitrate=fmt.get('max_bitrate'))

            elif typ == 'subtitle':
                return SubtitleStreamTemplate(codec=trackformat)
        else:
            raise Exception('No such format')

class TargetContainerGenerator(object):
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
            self.subtite_accepted_languages = config['Languages'].get('subtitle')
            self.config = config

        else:
            raise Exception('Unsupported container type')

    def build_target_container(self, sourcecontainer):
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

        return ctn



class IStreamGenerator(metaclass=ABCMeta):
    """Interface for stream generators. TargetStreams can be built in 2 different ways:
    1) The stream can be copied from a source stream. This does not involve a template.
    2) The stream can be checked against the template and its parameters adjusted accordingly
    In any case, we always need the source index to be able to map the targetstream to the source stream"""
    @staticmethod
    @abstractmethod
    def copystream(stream):
        pass

    @staticmethod
    @abstractmethod
    def conformtotemplate(stream, template):
        pass


class StreamGeneratorFactory(IStreamGenerator):

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
                                     sourceindex=stream.index,
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

            if template.max_bitrate and stream.bitrate and stream.bitrate > template.max_bitrate * 1000:
                bitrate = template.max_bitrate
                willtranscode = True
            else:
                bitrate = stream.bitrate / 1000

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
                                     willtranscode=willtranscode)


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
    validstreams = []
    for stream in streamlist:
        if stream.language in languagelist:
            validstreams.append(stream)

    if not validstreams and relax is True:
        return streamlist
    else:
        return validstreams


class VideoStreamTemplate(object):
    def __init__(self,
                 codec: str,
                 pix_fmts: list,
                 max_bitrate: int,
                 max_height: int,
                 max_width: int,
                 profiles: list,
                 max_level: int):

        self.codec = codec
        self.pix_fmts = pix_fmts
        self.max_bitrate = max_bitrate
        self.max_height = max_height
        self.max_width = max_width
        self.profiles = profiles
        self.max_level = max_level


class AudioStreamTemplate(object):
    def __init__(self, codec: str, max_channels: int, max_bitrate: int):
        self.codec = codec
        self.max_channels = max_channels
        self.max_bitrate = max_bitrate


class SubtitleStreamTemplate(object):
    def __init__(self, codec: str):
        self.codec = codec



class MissingFormatError(Exception):
    pass

if __name__ == '__main__':
    import configuration
    import converter.ffmpeg2
    cfgmgr = configuration.cfgmgr()
    cfgmgr.load('defaults.ini')
    cfg = cfgmgr.cfg
    Tg = TargetContainerGenerator(cfg, 'mp4')


    ff = converter.ffmpeg2.FFMpeg('/usr/local/bin/ffmpeg', '/usr/local/bin/ffprobe')
    SourceContainer = ff.probe('/Users/jon/Downloads/Geostorm 2017 1080p FR EN X264 AC3-mHDgz.mp4')
    TargetContainer = Tg.build_target_container(sourcecontainer=SourceContainer)

    print('yeah')