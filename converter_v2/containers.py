import copy
from typing import Union, Optional, List
from collections import Counter
from converter_v2.encoders import SubtitleCopy
from converter_v2.streamoptions import Disposition
from converter_v2.streams import AudioStream, VideoStream, SubtitleStream, StreamFactory, Stream, Streams
from converter_v2.templates import Templates
import logging

log = logging.getLogger(__name__)


class Container(object):
    supported_formats = ['mp4', 'matroska']

    def __init__(self, fmt, allow_identical=False):
        self.format = fmt
        self._audio_streams = {}
        self._video_streams = {}
        self._subtitle_streams = {}
        self._streams = {}
        self.allow_identical = allow_identical
        self._audio_counter = 0
        self._video_counter = 0
        self._subtitle_counter = 0
        self.stream_counter = 0
    def add_stream(self, stream: Union[VideoStream, AudioStream, SubtitleStream]):
        if isinstance(stream, VideoStream):
            self._video_streams.update(stream)
        elif isinstance(stream, AudioStream):
            self._audio_streams.append(stream)
        elif isinstance(stream, SubtitleStream):
            self._subtitle_streams.append(stream)
        else:
            raise TypeError('Streams can only be one of VideoStream, AudioStream and SubtitleStream')

    @property
    def video(self):
        return self._video_streams

    @property
    def audio(self):
        return self._audio_streams

    @property
    def subtitle(self):
        return self._subtitle_streams

    @property
    def streams(self):
        return [*self._video_streams, *self._audio_streams, *self._subtitle_streams]

    def __iter__(self):
        for s in self.streams:
            yield s

    def __len__(self):
        return len(self.streams)

    def __eq__(self, other):
        if not isinstance(other, Container):
            return False

        if (Counter(self.video) == Counter(other.video) and
                Counter(self.audio) == Counter(other.audio) and
                Counter(self.subtitle) == Counter(other.subtitle) and self.format == other.format):
            return True

        return False

    def container_from_ffprobe(self, filepath, ffmpegpath, ffprobepath):
        from converter_v2 import ffmpeg

        ff = ffmpeg.FFMpeg(ffmpegpath, ffprobepath)
        parser = ff.probe(filepath)

        self.format = Container(parser.format)

        for idx in range(len(parser.streams)):

            if parser.codec_type(idx) == 'video':
                v = VideoStream(allow_multiple=False)
                v.add_option(parser.codec(idx),
                             parser.pix_fmt(idx),
                             parser.height(idx),
                             parser.width(idx),
                             parser.bitrate(idx),
                             parser.disposition(idx),
                             parser.level(idx),
                             parser.profile(idx))
                self.add_stream(v, idx)

            elif parser.codec_type(idx) == 'audio':
                a = AudioStream(allow_multiple=False)
                a.add_option(parser.codec(idx),
                             parser.channels(idx),
                             parser.language(idx),
                             parser.bitrate(idx),
                             parser.disposition(idx))
                self.add_stream(a, idx)

            elif parser.codec_type(idx) == 'subtitle':
                s = SubtitleStream(allow_multiple=False)
                s.add_option(parser.codec(idx),
                             parser.language(idx),
                             parser.disposition(idx))
                self.add_stream(s, idx)


class LinkedContainer(object):
    """
    Linked Container enable to link source streams and target streams, in pairs, so that they
    can be processed one pair at a time to determine the options necessary to encode the source stream
    into the target stream.
    """

    def __init__(self, target):
        self.fmt = target
        self._stream_pairs = list()
        self.audio_stream_count = 0
        self.video_stream_count = 0
        self.subtitle_stream_count = 0

    @property
    def stream_pairs(self):
        return self._stream_pairs

    def add_stream_pairs(self, pair: List[Union[list, Stream]]):
        if len(pair[0]) != 2:
            raise Exception('Not acceptable')
        assert isinstance(pair[0][1], type(pair[1]))

        if isinstance(pair[1], AudioStream):
            self._add_audio_pair(pair)
        elif isinstance(pair[1], VideoStream):
            self._add_video_pair(pair)
        elif isinstance(pair[1], SubtitleStream):
            self._add_subtitle_pair(pair)

    def _add_audio_pair(self, pair: List[Union[list, Stream]], allow_duplicate=False):
        duplicate = False
        if not allow_duplicate:
            for stream_pair in self.audio_stream_pairs:
                (_, _), (_, target_stream) = stream_pair
                if target_stream == pair[1]:
                    duplicate = True
                    log.debug('Duplicate detected %s: %s', str(pair[1]), str(target_stream))
                    break

        if not duplicate:
            self._stream_pairs.append([pair[0], [self.audio_stream_count, pair[1]]])
            self.audio_stream_count += 1

    def _add_video_pair(self, pair: List[Union[list, Stream]], allow_duplicate=False):
        self._stream_pairs.append([pair[0], [self.video_stream_count, pair[1]]])
        self.video_stream_count += 1

    def _add_subtitle_pair(self, pair: List[Union[list, Stream]], allow_duplicate=False):

        self._stream_pairs.append([pair[0], [self.subtitle_stream_count, pair[1]]])
        self.subtitle_stream_count += 1

    @property
    def video_stream_pairs(self):
        return [pair for pair in self.stream_pairs if isinstance(pair[0][1], VideoStream)]

    @property
    def audio_stream_pairs(self):
        return [pair for pair in self.stream_pairs if isinstance(pair[0][1], AudioStream)]

    @property
    def subtitle_stream_pairs(self):
        return [pair for pair in self.stream_pairs if isinstance(pair[0][1], SubtitleStream)]

    def fix_disposition(self):
        for stream_type in [self.video_stream_pairs, self.audio_stream_pairs, self.subtitle_stream_pairs]:
            k = 0
            for (_, _,), (_, stream) in stream_type:
                disp_option = stream.options.get_option(Disposition)
                if disp_option:
                    thedisposition = disp_option.value
                    thedisposition['default'] = 1 if k == 0 else 0  # FIX THIS
                    stream.replace_options(Disposition(thedisposition))
                else:
                    stream.add_option(Disposition({'default': 1 if k == 0 else 0}))
                k += 1

    def __str__(self):

        from io import StringIO
        s = StringIO()

        for pair in self.stream_pairs:
            (source_index, source_stream), (target_index, target_stream) = pair
            s.write(f'\nSource stream #{source_index} -> Target {target_stream.__class__.__name__} #{target_index}\n')
            for opt_name, opt in source_stream.options.items():
                if opt_name in target_stream.options:
                    s.write(f'{opt_name}: {opt.value} -> {target_stream.options[opt_name].value}\n')
                else:
                    s.write(f'{opt_name}: {opt.value} -> =\n')
            s.write('-' * 10)

        return s.getvalue()

    def remove_matching_stream_pairs(self, *streams: Union[AudioStream, VideoStream, SubtitleStream]):
        """
        Removes stream pairs whose target_stream matches any of the streams specified in *streams
        :param streams:  AudioStream, VideoStream or SubtitleStream
        :return: None
        """
        newpairs = self._stream_pairs[:]

        for pair in self._stream_pairs:
            (_, _), (target_index, target_stream) = pair
            for _filter in streams:
                if isinstance(target_stream, type(_filter)) and target_stream != _filter:
                    newpairs.remove(pair)
        p = []
        for idx, pair in enumerate(newpairs):
            p.append((pair[0], (idx, pair[1][1])))

        return p

    def from_templates(self, container: Container, templates: Templates):

        assert isinstance(templates, Templates)

        for idx, stream in container.streams.items():
            target_stream = StreamFactory.get_stream_by_type(stream)
            tpl = templates.get_template_by_codec(stream)
            if not tpl:
                tpl = templates.get_default(stream)

            for option_name, option in stream.options.items():
                # If we find an option in the template that fits the source stream, select the source stream option
                # If there are no corresponding option in the template stream, select the source stream option
                template_options = tpl.options.get_option(option_name)
                target_option = None

                if template_options:
                    for tpl_opt in template_options:
                        if isinstance(tpl_opt.value, (int, float)):
                            if tpl_opt and tpl_opt >= option:
                                target_option = copy.copy(option)
                                break
                        else:
                            if tpl_opt and tpl_opt == option:
                                target_option = copy.copy(option)
                                break
                    if not target_option:
                        target_option = copy.copy(template_options[0])
                else:
                    target_option = copy.copy(option)

                target_stream.add_option(target_option)

            if len(target_stream.options) > 0:
                self.add_stream_pairs([[idx, stream], target_stream])
