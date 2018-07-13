from converter_v2.streamformats import StreamFormatFactory
from converter_v2.containers import Container
from converter_v2.streamoptions import Language, MetadataOption, Disposition
from converter_v2.streams import StreamFactory, VideoStream, AudioStream, SubtitleStream
from converter_v2.encoders import _FFMpegCodec, Encoders
from typing import List
import logging

log = logging.getLogger(__name__)


class OptionBuilder(object):
    """Builds a list of options suitable to pass to subprocess.Popen"""
    image_subtitle_codecs = ['hdmv_pgs_subtitle']
    bad_audio_codecs = ['truehd']
    bad_codecs = ['truehd']

    def __init__(self, container: Container, target):
        self.container = container
        self.mapping = list()  # This is the mapping
        self.target = target

        self.few_audio_tracks = True
        self.target_container = Container(target)

    def generate_mapping_2(self, stream_templates, stream_defaults, audio_languages, subtitle_languages,
                           compare_presets=None):

        for index, stream in self.container.streams.items():

            if stream.codec.value in self.bad_codecs:
                continue

            ignore = False
            if compare_presets is not None:
                ignore = compare_presets.get(stream.kind, False)

            codec = stream.codec
            if not codec:
                raise Exception('stream has no codec')

            if isinstance(stream, AudioStream):
                b = False
                for lng in audio_languages:
                    if lng == stream.options.get_unique_option(Language):
                        b = True
                        break

                if not b:
                    continue

            if stream.codec in stream_templates:  # TODO: this is where we should look for filters
                # If codec is in the available templates we need to check the options
                incompatible_options = stream.options.incompatible_options(stream_templates[codec])

                # if isinstance(stream, (AudioStream, SubtitleStream)) and incompatible_options.has_option(Language):
                #    # This means that if the languages do not match, then we skip the track
                #    continue

                target_stream = StreamFactory.get_stream_by_type(stream, stream.codec)
                if not ignore:
                    target_stream.add_options(*incompatible_options.options)

            else:
                # If it is not, we know we're going to transcode.
                codec, options = stream_defaults[stream.kind]
                target_stream = StreamFactory.get_stream_by_type(stream, codec)
                target_stream.add_options(*options)

            for opt in stream.options.options:
                if isinstance(opt, MetadataOption):
                    target_stream.add_options(opt)

            if isinstance(stream, SubtitleStream):
                # FFmpeg can't transcode from an image based codec into a text based codec.
                if stream.codec.value in self.image_subtitle_codecs and (
                        target_stream.codec.value not in self.image_subtitle_codecs):
                    continue

            target_index = self.target_container.add_stream(target_stream, duplicate_check=False)

            if target_index is not None:
                self.add_mapping_2(index, target_index)

    def add_mapping_2(self, source_index, target_index):

        try:
            stream = self.container.streams[source_index]
        except KeyError:
            return None

        assert isinstance(self.container.streams[source_index], self.target_container.streams[target_index].__class__)

        self.mapping.append((source_index, target_index))

    # def fix_disposition(self):
    #     video_counter = 0
    #     audio_counter = 0
    #     subtitle_counter = 0
    #     video_disp = {0: [], 1: []}
    #     audio_disp = {0: [], 1: []}
    #     subtitle_disp = {0: [], 1: []}
    #
    #
    #     for idx, stream in self.target_container.streams:
    #         disp = stream.options.get_unique_option(Disposition)
    #         if isinstance(stream, VideoStream):
    #             if disp and 'default' in disp:
    #                 video_disp[disp['default']].append(idx)
    #             else:
    #                 video_disp[0].append(idx)
    #         elif isinstance(stream, AudioStream):
    #             if disp and 'default' in disp:
    #                 audio_disp[disp['default']].append(idx)
    #             else:
    #                 audio_disp[0].append(idx)
    #         elif isinstance(stream, SubtitleStream):
    #             if disp and 'default' in disp:
    #                 subtitle_disp[disp['default']].append(idx)
    #             else:
    #                 subtitle_disp[0].append(idx)
    #
    #     if len(audio_disp[1]) == 0 and audio_disp[0]:
    #

    def prepare_encoders(self, encoders: Encoders, preferred_encoders: dict = None):
        video_counter = 0
        audio_counter = 0
        subtitle_counter = 0
        output = []
        preferred_encoders = {} if preferred_encoders is None else preferred_encoders

        if not self.mapping:
            raise Exception('Cannot prepaper encoders, no mapping has been generated')

        for m in self.mapping:
            source_index, target_index = m
            source_stream = self.container.streams[source_index]
            target_stream = self.target_container.streams[target_index]

            options_no_metadata = [o for o in target_stream.options if not isinstance(o, MetadataOption)]

            if source_stream.codec == target_stream.codec and (len(options_no_metadata) == 0):
                encoder = encoders.get_copy_encoder(target_stream.kind)()
            else:
                if target_stream.codec.value in preferred_encoders:
                    encoder = encoders.get_specific_encoder(preferred_encoders[target_stream.codec.value],
                                                            target_stream.codec.value)
                else:
                    encoder = encoders.get_encoder_from_stream_format(target_stream.codec.value)

            encoder.add_option(*target_stream.options)

            output.extend(['-map', f'0:{source_index}'])
            if isinstance(target_stream, VideoStream):
                output.extend(encoder.parse(video_counter))
                video_counter += 1
            elif isinstance(target_stream, AudioStream):
                output.extend(encoder.parse(audio_counter))
                audio_counter += 1
            elif isinstance(target_stream, SubtitleStream):
                output.extend(encoder.parse(subtitle_counter))
                subtitle_counter += 1

        output.extend(['-f', self.target_container.format])
        log.debug(' '.join(output))
        return output


    def generate_options_2(self, encoders: Encoders) -> list:
        if not self.mapping:
            raise Exception('Nothing in mapping')
        video_counter = 0
        audio_counter = 0
        subtitle_counter = 0
        output = []

        log.debug(str(self))
        for m in self.mapping:
            source_index, target_index = m
            target_stream = self.target_container.streams[target_index]
            stream = self.container.streams[source_index]

            fmt = StreamFormatFactory.get_format(target_stream.codec.value)
            options_no_metadata = [o for o in target_stream.options if not isinstance(o, MetadataOption)]

            if stream.codec == target_stream.codec and (len(options_no_metadata) == 0):
                encoder = fmt.get_encoder('copy')
            else:
                encoder = fmt.get_encoder('default')

            for _enc in encoders.encoders:
                if _enc.__class__ == encoder.__class__:
                    encoder = _enc
                    break

            encoder.add_option(*target_stream.options)

            output.extend(['-map', f'0:{source_index}'])
            if isinstance(stream, VideoStream):
                output.extend(encoder.parse(video_counter))
                video_counter += 1
            elif isinstance(stream, AudioStream):
                output.extend(encoder.parse(audio_counter))
                audio_counter += 1
            elif isinstance(stream, SubtitleStream):
                output.extend(encoder.parse(subtitle_counter))
                subtitle_counter += 1

        output.extend(['-f', self.target_container.format])
        return output

    def __str__(self):
        from io import StringIO
        s = StringIO()
        for m in self.mapping:
            source_index, target_index = m
            source_stream = self.container.streams[source_index]
            target_stream = self.target_container.streams[target_index]
            p = f'{source_index} : {source_stream.codec} -> {target_index}: {target_stream.codec}\n'
            s.write(p)
            for opt in source_stream.options.options:
                topt = target_stream.options.get_unique_option(opt.__class__)
                if topt:
                    p = f'    {opt} -> {topt}\n'
                else:
                    p = f'    {opt} -> same\n'
                s.write(p)
            s.write('-' * 10 + '\n')

        return s.getvalue()
