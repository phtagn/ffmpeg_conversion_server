from converter_v2.streamformats import StreamFormatFactory
from converter_v2.containers import Container
from converter_v2.streamoptions import Codec, Map, Filter, Height, Width, Filters, Scale
# from converter_v2.streams import Stream

import logging

log = logging.getLogger(__name__)


class OptionBuilder(object):
    """Builds a list of options suitable to pass to subprocess.Popen"""

    def __init__(self, container: Container, stream_templates):
        self.container = container
        self.templates = stream_templates
        self.encoders = None

    def generate_mapping(self):
        for _, stream in self.container.streams.items():
            codec = stream.codec
            if not codec:
                raise Exception('stream has no codec')

            if stream.codec in self.templates:

                oooo = stream.options.incompatible_options(self.templates[codec])
                print('yeah')
            else:
                pass
