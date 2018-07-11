from converter_v2.streamformats import StreamFormatFactory
from converter_v2.containers import Container
from converter_v2.streamoptions import Language, MetadataOption, Disposition
from converter_v2.streams import StreamFactory, VideoStream, AudioStream, SubtitleStream
from converter_v2.encoders import _FFMpegCodec, Ac3, Dts, Aac
from typing import List
import logging

log = logging.getLogger(__name__)


class OptionBuilder(object):
    """Builds a list of options suitable to pass to subprocess.Popen"""
    image_subtitle_codecs = ['hdmv_pgs_subtitle']
    bad_audio_codecs = ['truehd']
    bad_codecs = ['truehd']

    def __init__(self, container: Container, target, codec_priority=None):
        self.container = container
        self.mapping = list()  # This is the mapping
        self.target = target
        self.codec_priority = {Dts: 5,
                               Ac3: 4,
                               Aac: 1}
        self.few_audio_tracks = True
        self.target_container = Container(target)

    def is_duplicate(self, index, stream, mode='strict'):

        for (idx, _), target_stream in self.mapping:
            # if mode == 'strict':
            #    if stream == target_stream and idx == index:
            #        return True
            # else:
            if stream == target_stream:
                return True
        return False

    def generate_mapping(self, stream_templates, stream_defaults, ignore_video=False, ignore_audio=False,
                         ignore_subtitle=False):

        for index, stream in self.container.streams.items():
            if stream.codec.value in self.bad_codecs:
                continue

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

            if isinstance(stream, SubtitleStream):
                # FFmpeg can't transcode from an image based codec into a text based codec.
                if stream.codec.value in self.image_subtitle_codecs and (
                        target_stream.codec.value not in self.image_subtitle_codecs):
                    continue

            self.add_mapping(index, target_stream, duplicate_check=True)

    def generate_mapping_2(self, stream_templates, stream_defaults, ignore_video=False, ignore_audio=False,
                           ignore_subtitle=False):

        for index, stream in self.container.streams.items():
            if stream.codec.value in self.bad_codecs:
                continue

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

                if isinstance(stream, (AudioStream, SubtitleStream)) and incompatible_options.has_option(Language):
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

        assert isinstance(self.container.streams[source_index], self.container.streams[target_index].__class__)

        self.mapping.append((source_index, target_index))

    def add_mapping(self, source_stream_index, target_stream, duplicate_check=True):
        assert isinstance(target_stream, (AudioStream, VideoStream, SubtitleStream))

        try:
            stream = self.container.streams[source_stream_index]
        except KeyError:
            return None

        assert isinstance(self.container.streams[source_stream_index], target_stream.__class__)

        if not duplicate_check or not self.is_duplicate(source_stream_index, target_stream, mode='loose'):
            self.mapping.append((
                (source_stream_index, stream),
                target_stream))
        # elif not duplicate_check:
        #    self.mapping.append((
        #        (source_stream_index, stream),
        #        target_stream))

    # def fix_disposition(self):
    #     video_counter = 0
    #     audio_counter = 0
    #     subtitle_counter = 0
    #     video_disp = {0: [], 1: []}
    #     audio_disp = {0: [], 1: []}
    #     subtitle_disp = {0: [], 1: []}
    #
    #     for m in self.mapping:
    #         disp = 0
    #         (_, _), target_stream = m
    #         if target_stream.options.has_option(Disposition) and True:
    #             disposition = target_stream.options.get_unique_option(Disposition)
    #             if isinstance(target_stream, VideoStream):
    #                 video_disp[disposition.get('default', 0)] += 1
    #             if isinstance(target_stream, AudioStream):
    #                 audio_disp[disposition.get('default', 0)] += 1
    #             if isinstance(target_stream, SubtitleStream):
    #                 subtitle_disp[disposition.get('default', 0)] += 1

    def generate_options(self, encoders: List[_FFMpegCodec]) -> list:
        if not self.mapping:
            raise Exception('Nothing in mapping')
        video_counter = 0
        audio_counter = 0
        subtitle_counter = 0
        output = []

        print(str(self))
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

    def generate_options_2(self, encoders: List[_FFMpegCodec]) -> list:
        if not self.mapping:
            raise Exception('Nothing in mapping')
        video_counter = 0
        audio_counter = 0
        subtitle_counter = 0
        output = []

        print(str(self))
        for m in self.mapping:
            source_index, target_index = m
            target_stream = self.target_container.streams[target_index]
            stream = self.container.streams[source_index]

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
        log.debug(' '.join(output))
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
