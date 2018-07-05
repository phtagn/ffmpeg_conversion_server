from converter_v2.streamformats import StreamFormatFactory
from converter_v2.streamoptions import Codec, Map, Filter, Height, Width, Filters, Scale
#from converter_v2.streams import Stream

import logging
log = logging.getLogger(__name__)


class OptionBuilder(object):
    """Builds a list of options suitable to pass to subprocess.Popen"""
    def __init__(self):
        pass

    def build_options(self, lctn, preferred_codec: dict, *encoders):
        """
        Main method, outputs the list of options
        :param lctn: a LinkedContainer
        :param preferred_codec: a dictionary of the form {StreamFormat: encoder}. It is used to indicate which is
        the preferred encoder for a particular stream format. For example, an aac track may be produced by the native encoder
        (aac), or libfdk_aac. In order to produce using libfdk_aac, preferred_encoder must be set to {aac: fdk_aac}.
        The list of encoders for a particular stream is found in the streamformat object (in the streamformat module), in the
        encoders class variable.
        :param encoders: encoders with options
        :return:
        """
        opts = []
        for pair in lctn.stream_pairs:
            (source_idx, source_stream), (target_idx, target_stream) = pair
            log.debug(f'\nSource:, {source_stream}\nTarget:, {target_stream}')

            fmt = target_stream.get_option_by_type(Codec).value

            streamformat = StreamFormatFactory.get_format(fmt)

            enc = None

            if fmt in preferred_codec:
                enc = preferred_codec[fmt]

            # for k, option in source_stream.options.items():
            #    if k in target_stream.options:
            #        if target_stream.options[k] == option:
            #            del target_stream.options[k]

            if source_stream == target_stream and not target_stream.get_option_by_type(Filter):
                encoder = streamformat.get_encoder('copy', *target_stream.options.values(), Map((0, source_idx)))
            else:
                encoder = streamformat.get_encoder(enc, *target_stream.options.values(), Map((0, source_idx)))

            for enco in encoders:
                if type(encoder) == type(enco):
                    encoder.add_option(*enco.options)

            opts.extend(encoder.parse(target_idx))

        return opts


