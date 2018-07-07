from converter_v2.streamformats import StreamFormatFactory
from converter_v2.containers import Container
from converter_v2.streamoptions import Language, Codec
from converter_v2.streams import StreamFactory

import logging

log = logging.getLogger(__name__)


class OptionBuilder(object):
    """Builds a list of options suitable to pass to subprocess.Popen"""

    def __init__(self, container: Container, stream_templates, stream_defaults, encoders):
        self.container = container
        self.templates = stream_templates
        self.stream_defaults = stream_defaults
        self.encoders = encoders
        self.mapping = list()

    def generate_mapping(self):

        for _, stream in self.container.streams.items():
            codec = stream.codec
            if not codec:
                raise Exception('stream has no codec')

            if stream.codec in self.templates:  # TODO: this is where we should look for filters
                # If codec is in the available templates we need to check the options
                incompatible_options = stream.options.incompatible_options(self.templates[codec])
                if incompatible_options.has_option(Language):
                    continue

                target_stream = StreamFactory.get_stream_by_type(stream, stream.codec)
                target_stream.add_options(*incompatible_options.options)
                self.mapping.append((stream, target_stream))

            else:
                # If it is not, we know we're going to transcode.
                codec, options = self.stream_defaults[stream.kind]
                target_stream = StreamFactory.get_stream_by_type(stream, codec)
                target_stream.add_options(*options.options)
                self.mapping.append((stream, target_stream))

    def generate_options(self):
        if not self.mapping:
            raise Exception('Nothing in mapping')

        for stream, target_stream in self.mapping:
            fmt = StreamFormatFactory.get_format(target_stream.codec.value)

            if stream.codec == target_stream.codec:
                encoder = fmt.get_encoder('copy')
                encoder.add_option(*target_stream.options.options)
            else:
                encoder = fmt.get_encoder('default')
                encoder.add_option(*target_stream.options.options)

