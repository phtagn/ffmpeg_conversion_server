from converter_v2.streamformats import StreamFormatFactory
from converter_v2.containers import Container
from converter_v2.streamoptions import Language, MetadataOption
from converter_v2.streams import StreamFactory, VideoStream, AudioStream, SubtitleStream
from converter_v2.encoders import _FFMpegCodec
from typing import List
import logging

log = logging.getLogger(__name__)


class OptionBuilder(object):
    """Builds a list of options suitable to pass to subprocess.Popen"""
    bad_codecs = []

    def __init__(self, container: Container, target):
        self.container = container
        self.mapping = list()
        self.target = target

    def is_duplicate(self, index, stream, mode='strict'):

        for (idx, _), target_stream in self.mapping:
            if mode == 'strict':
                if stream == target_stream and idx == index:
                    return True
            else:
                if stream == target_stream:
                    return True
        return False

    def generate_mapping(self, stream_templates, stream_defaults, ignore_video=False, ignore_audio=False,
                         ignore_subtitle=False):

        for index, stream in self.container.streams.items():
            ignore = False
            if isinstance(stream, VideoStream):
                ignore = ignore_video
            elif isinstance(stream, AudioStream):
                ignore = ignore_audio
            elif isinstance(stream, SubtitleStream):
                ignore = ignore_subtitle

            codec = stream.codec
            if not codec:
                raise Exception('stream has no codec')

            if stream.codec in stream_templates:  # TODO: this is where we should look for filters
                # If codec is in the available templates we need to check the options
                incompatible_options = stream.options.incompatible_options(stream_templates[codec])

                if incompatible_options.has_option(Language):
                    # This means that if the languages do not match, then we skip the track
                    continue

                target_stream = StreamFactory.get_stream_by_type(stream, stream.codec)
                if not ignore:
                    target_stream.add_options(*incompatible_options.options)

            else:
                # If it is not, we know we're going to transcode.
                codec, options = stream_defaults[stream.kind]
                target_stream = StreamFactory.get_stream_by_type(stream, codec)
                target_stream.add_options(*options.options)

            for opt in stream.options.options:
                if isinstance(opt, MetadataOption):
                    target_stream.add_options(opt)

            self.add_mapping(index, target_stream)

    def add_mapping(self, source_stream_index, target_stream, mode='strict'):
        assert isinstance(target_stream, (AudioStream, VideoStream, SubtitleStream))

        try:
            stream = self.container.streams[source_stream_index]
        except KeyError:
            return None

        assert isinstance(self.container.streams[source_stream_index], target_stream.__class__)

        if not self.is_duplicate(source_stream_index, target_stream, mode=mode):
            self.mapping.append((
                (source_stream_index, stream),
                target_stream))

    def generate_options(self, encoders: List[_FFMpegCodec]) -> list:
        if not self.mapping:
            raise Exception('Nothing in mapping')
        video_counter = 0
        audio_counter = 0
        subtitle_counter = 0
        output = []

        for (idx, stream), target_stream in self.mapping:

            fmt = StreamFormatFactory.get_format(target_stream.codec.value)
            options_no_metadata = [o for o in target_stream.options.options if not isinstance(o, MetadataOption)]

            if stream.codec == target_stream.codec and (len(options_no_metadata) == 0):
                encoder = fmt.get_encoder('copy')
            else:
                encoder = fmt.get_encoder('default')

            for _enc in encoders:
                if _enc.__class__ == encoder.__class__:
                    encoder = _enc
                    break

            encoder.add_option(*target_stream.options.options)

            output.extend(['-map', f'0:{idx}'])
            if isinstance(stream, VideoStream):
                output.extend(encoder.parse(video_counter))
                video_counter += 1
            elif isinstance(stream, AudioStream):
                output.extend(encoder.parse(audio_counter))
                audio_counter += 1
            elif isinstance(stream, SubtitleStream):
                output.extend(encoder.parse(subtitle_counter))
                subtitle_counter += 1

        output.extend(['-f', self.target])
        log.debug(' '.join(output))
        return output
