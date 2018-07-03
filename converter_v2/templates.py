from typing import Union

from converter_v2.streamoptions import Codec
from converter_v2.streams import VideoStream, AudioStream, SubtitleStream, Stream
import logging
log = logging.getLogger(__name__)

class Template(Stream):
    """Class for stream templates. The only difference between templates and streams is that
    templates may allow for an option to be present multiple times. This is to avoid having
    to build a template for every different permutation of options around a stream format. For example
    a user may allow 3 profiles in H264 and 2 pix formats, which would mean 6 templates.
    Templates are centered on a """

    def add_option(self, *options):
        for opt in options:
            if type(opt) in self.supported_options and opt.value is not None:
                if opt.__class__.__name__ not in self._options:
                    self._options.update({opt.__class__.__name__: [opt]})
                else:
                    self._options[opt.__class__.__name__].append(opt)


class VideoStreamTemplate(Template):
    supported_options = VideoStream.supported_options.copy()


class AudioStreamTemplate(Template):
    supported_options = AudioStream.supported_options.copy()


class SubtitleStreamTemplate(Template):
    supported_options = SubtitleStream.supported_options.copy()


class StreamTemplateFactory(object):

    @staticmethod
    def get_stream_template(stream: Stream, *options) -> Union[VideoStreamTemplate,
                                                               AudioStreamTemplate,
                                                               SubtitleStreamTemplate]:
        if isinstance(stream, VideoStream):
            return VideoStreamTemplate(*options)
        elif isinstance(stream, AudioStream):
            return AudioStreamTemplate(*options)
        elif isinstance(stream, SubtitleStream):
            return SubtitleStreamTemplate(*options)


class Templates(object):

    def __init__(self):
        self._audio_templates = []
        self._video_templates = []
        self._subtitle_templates = []

    def add_template(self, tpl):
        assert isinstance(tpl, (AudioStreamTemplate, VideoStreamTemplate, SubtitleStreamTemplate))
        if isinstance(tpl, VideoStreamTemplate):
            self._video_templates.append(tpl)
        elif isinstance(tpl, AudioStreamTemplate):
            self._audio_templates.append(tpl)
        elif isinstance(tpl, SubtitleStreamTemplate):
            self._subtitle_templates.append(tpl)

    @property
    def video_templates(self):
        return self._video_templates

    @property
    def audio_templates(self):
        return self._audio_templates

    @property
    def subtitle_templates(self):
        return self._subtitle_templates

    @property
    def default_audio_template(self):
        try:
            return self._audio_templates[0]
        except IndexError:
            return None

    @property
    def default_video_template(self):
        try:
            return self._video_templates[0]
        except IndexError:
            return None

    @property
    def default_subtitle_template(self):
        try:
            return self._subtitle_templates[0]
        except IndexError:
            return None

    def get_default(self, stream: Union[AudioStream, VideoStream, SubtitleStream]):
        assert isinstance(stream, (AudioStream, VideoStream, SubtitleStream))
        if isinstance(stream, VideoStream):
            return self._video_templates[0]
        elif isinstance(stream, AudioStream):
            return self._audio_templates[0]
        elif isinstance(stream, SubtitleStream):
            return self._subtitle_templates[0]

    def get_template_by_name(self, name: str):
        if name.lower() == 'video':
            return self._video_templates
        elif name.lower() == 'audio':
            return self._audio_templates
        elif name.lower() == 'subtitle':
            return self._subtitle_templates

    def get_template_by_stream_type(self, stream: Union[AudioStream, VideoStream, SubtitleStream]):
        assert isinstance(stream, (AudioStream, VideoStream, SubtitleStream))
        if isinstance(stream, VideoStream):
            return self._video_templates
        elif isinstance(stream, AudioStream):
            return self._audio_templates
        elif isinstance(stream, SubtitleStream):
            return self._subtitle_templates

    def get_template_by_codec(self, stream):
        assert isinstance(stream, (AudioStream, VideoStream, SubtitleStream))
        tpls = self.get_template_by_stream_type(stream)
        for tpl in tpls:
            for cdc in tpl.get_option_by_type(Codec):
                if cdc == stream.get_option_by_type(Codec):
                    return tpl

        return None
