from typing import Optional, List, Tuple
from converter_v2.encoders import *
from converter_v2.streamoptions import *
from converter_v2.streamformats import StreamFormatFactory
import logging
import copy
from abc import ABC
from inspect import isclass

logging.basicConfig(filename='server.log', filemode='w', level=logging.DEBUG)
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class Stream(ABC):
    """
    Generic stream class, it is not to be instantiated directly. Use concrete classes VideoStream, AudioStream and SubtitleStream
    """
    supported_options = []
    multiple = []

    def __init__(self, *options: IStreamOption):
        self._options = {}
        self.add_option(*options)

    def add_option(self, *options):
        for opt in options:
            if type(opt) in self.supported_options:
                if opt.__class__.__name__ not in self._options:
                    self._options.update({opt.__class__.__name__: opt})

    @property
    def options(self):
        return self._options

    def replace_options(self, *options):
        for opt in options:
            assert isinstance(opt, IStreamOption)
            if opt.__class__.__name__ in self.options:
                del self.options[opt.__class__.__name__]
                self.add_option(opt)

    def get_option_by_name(self, name):
        return self.options.get(name, None)

    def get_option_by_type(self, option):
        #assert isinstance(option, IStreamOption)
        val = None
        try:
            val = self.options[option.__name__]
        except KeyError:
            pass
        try:
            val = self.options[option.__class__.__name__]
        except KeyError:
            pass

        return val

    def remove_option(self, *options: IStreamOption):
        for option in options:
            for k, opt in self.options:
                if opt == option:
                    del self.options[k]

    def strict_eq(self, other):
        r = False
        if isinstance(other, type(self)):
            for name, opt in self.options.items():
                if other.get_option_by_name(name):
                    if other.options[name] == opt:
                        r = True
                    else:
                        r = False
                        break
                else:
                    r = False
                    break
        return r

    def __eq__(self, other):
        """Compares streams by comparing the value of options
        attached to them. IMPORTANT: If the option is missing in other, a match will be
        assumed and the comparison will return True. This is a design decision
        so that when building streams from templates, you don't have to specify every single option
        present in a source stream built from a ffprobe."""
        r = False
        if isinstance(other, type(self)):
            for name, opt in self.options.items():
                if other.get_option_by_name(name):
                    if other.options[name] == opt:
                        r = True
                    else:
                        r = False
                        break
                else:
                    r = True
        return r

    def __copy__(self):
        new = type(self)()
        for opt in self.options.values():
            newopt = copy.copy(opt)
            new.add_option(newopt)
        return new

    def __str__(self):
        output = {k: self.options[k].value for k in self.options}
        return str(output)


class StreamFactory(object):

    @classmethod
    def get_stream_by_type(cls, stream: Stream) -> Stream:
        assert isinstance(stream, (VideoStream, AudioStream, SubtitleStream))
        this_module = __import__(__name__)
        stream_class = getattr(this_module, str(stream.__class__.__name__))

        return stream_class([])


class VideoStream(Stream):
    supported_options = [Codec, PixFmt, Bitrate, Disposition, Height, Width, Level, Profile]

    def __init__(self, *options):
        super(VideoStream, self).__init__(*options)
        self.type = 'video'

    def __copy__(self):
        super(VideoStream, self).__copy__()


class AudioStream(Stream):
    supported_options = [Codec, Channels, Language, Disposition, Bitrate]

    def __init__(self, *options):
        super(AudioStream, self).__init__(*options)
        self.type = 'audio'

    def __copy__(self):
        super(AudioStream, self).__copy__()


class SubtitleStream(Stream):
    supported_options = [Codec, Language, Disposition]

    def __init__(self, *options):
        super(SubtitleStream, self).__init__(*options)
        self.type = 'subtitle'


class Container(object):
    supported_formats = ['mp4', 'matroska']

    def __init__(self, fmt):
        if fmt in self.supported_formats:
            self.format = fmt
            self._streams = {}

        else:
            raise Exception('Format %s not supported', fmt)

    def add_stream(self, stream: Union[AudioStream, VideoStream, SubtitleStream],
                   stream_number: Optional[int] = 0) -> int:
        """
        Add a stream to the list of streams in the Container. Streams can be with a specified stream
        number, or the method will insert at the next available stream number.
        :param stream: A concrete instance of Stream (VideoStream, AudioStream or SubtitleStream)
        :param stream_number: optional, insert the stream with the specified stream number
        :return: the stream number where the stream was inserted
        """
        assert isinstance(stream, (VideoStream, AudioStream, SubtitleStream))
        if stream_number:
            sn = stream_number
        else:
            sn = len(self._streams)
            sn += 1 if sn > 0 else 0
        if stream_number in self._streams.keys():
            log.info('Replacing stream %s', stream_number)

        self._streams.update({sn: stream})
        return sn

    @property
    def audio_streams(self):
        return {k: v for k, v in self._streams.items() if isinstance(v, AudioStream)}

    @property
    def subtitle_streams(self):
        return {k: v for k, v in self._streams.items() if isinstance(v, SubtitleStream)}

    @property
    def video_streams(self):
        return {k: v for k, v in self._streams.items() if isinstance(v, VideoStream)}

    @property
    def streams(self):
        return self._streams

    def get_stream(self, index) -> Optional[Union[VideoStream, AudioStream, SubtitleCopy]]:
        """
        Return the stream at the index, or None of the stream does not exist.
        :param index: int, the index of the stream
        :return: Stream
        """
        if index in self._streams:
            return self._streams.get(index, None)

    def remove_matching_streams(self, *streams: Union[VideoStream, AudioStream, SubtitleStream]):
        """
        Removes stream that matches any of the streams specified in *streams. There is no renumbering.
        :param streams:  AudioStream, VideoStream or SubtitleStream
        :return: None
        """
        newstreams = self._streams.copy()
        for k, v in self._streams.items():
            for sfilter in streams:
                if isinstance(v, type(sfilter)) and v != sfilter:
                    del newstreams[k]

        self._streams = newstreams

    def keep_matching_streams(self, *streams: Union[VideoStream, AudioStream, SubtitleStream]):
        """
        Removes all streams that do not match the condition. There is no renumbering.
        :param streams: VideoStream, AudioStream or SubtitleStream
        :return: None
        """
        newstreams = {}
        for k, v in self._streams.items():
            for sfilter in streams:
                if isinstance(v, type(sfilter)):
                    if v == sfilter:
                        newstreams.update({k: v})
                else:
                    newstreams.update({k: v})

        self._streams = newstreams

    def __eq__(self, other):
        if isinstance(other, Container):
            if len(self.streams) != len(other.streams):
                return False

            for idx, stream in self.video_streams.items():
                if other.video_streams[idx] != stream:
                    return False

            for idx, stream in self.audio_streams.items():
                if other.audio_streams[idx] != stream:
                    return False

            for idx, stream in self.subtitle_streams.items():
                if other.subtitle_streams[idx] != stream:
                    return False

            return True

        return False


class VideoStreamTemplate(VideoStream):
    """Templates for video streams. They are different from VideoStreams in that they allow for the same option
    to be present multiple times. StreamTemplates are used to be compared to VideoStreams. See ContainerFactory for
    more information"""

    def add_option(self, *options):
        for opt in options:
            if type(opt) in self.supported_options:
                if opt.__class__.__name__ not in self._options:
                    self._options.update({opt.__class__.__name__: [opt]})
                else:
                    self._options[opt.__class__.__name__].append(opt)


class AudioStreamTemplate(AudioStream):
    """Templates for video streams. They are different from VideoStreams in that they allow for the same option
        to be present multiple times. StreamTemplates are used to be compared to VideoStreams. See ContainerFactory for
        more information"""

    def add_option(self, *options):
        for opt in options:
            if type(opt) in self.supported_options:
                if opt.__class__.__name__ not in self._options:
                    self._options.update({opt.__class__.__name__: [opt]})
                else:
                    self._options[opt.__class__.__name__].append(opt)


class SubtitleStreamTemplate(SubtitleStream):
    """Templates for video streams. They are different from VideoStreams in that they allow for the same option
        to be present multiple times. StreamTemplates are used to be compared to VideoStreams. See ContainerFactory for
        more information"""

    def add_option(self, options):
        for opt in options:
            if type(opt) in self.supported_options:
                if opt.__class__.__name__ not in self._options:
                    self._options.update({opt.__class__.__name__: [opt]})
                else:
                    self._options[opt.__class__.__name__].append(opt)


class ContainerFactory(object):

    @staticmethod
    def container_from_ffprobe(filepath, ffmpegpath, ffprobepath) -> Container:
        from converter_v2 import ffmpeg

        ff = ffmpeg.FFMpeg(ffmpegpath, ffprobepath)
        parser = ff.probe(filepath)

        if 'matroska' in parser.format:
            ctn = Container('matroska')
        elif 'mp4' in parser.format:
            ctn = Container('mp4')
        else:
            ctn = Container(parser.format)

        for idx in range(len(parser.streams)):

            if parser.codec_type(idx) == 'video':
                v = VideoStream(parser.codec(idx),
                                parser.pix_fmt(idx),
                                parser.height(idx),
                                parser.width(idx),
                                parser.bitrate(idx),
                                parser.disposition(idx),
                                parser.level(idx),
                                parser.profile(idx))
                ctn.add_stream(v, idx)

            elif parser.codec_type(idx) == 'audio':
                a = AudioStream(parser.codec(idx),
                                parser.channels(idx),
                                parser.language(idx),
                                parser.bitrate(idx),
                                parser.disposition(idx))
                ctn.add_stream(a, idx)

            elif parser.codec_type(idx) == 'subtitle':
                s = SubtitleStream(parser.codec(idx),
                                   parser.language(idx),
                                   parser.disposition(idx))
                ctn.add_stream(s, idx)

        return ctn

    @staticmethod
    def container_from_template(container: Container, target: str,
                                templates: List[
                                    Union[AudioStreamTemplate, VideoStreamTemplate, SubtitleStreamTemplate]]):
        ctn = LinkedContainer(target)

        for idx, stream in container.streams.items():
            # Get a new stream of the same type as the input stream
            target_stream = StreamFactory.get_stream_by_type(stream)
            # Find the correct template for the stream considered
            template = None

            for tpl in templates:
                if issubclass(tpl.__class__, type(stream)):
                    template = tpl
                    break

            if not template:
                ctn.add_stream_pairs(((idx, stream), copy.copy(stream)))
                continue

            if not stream.options:
                raise Exception('No option in stream, cannot build')

            for option_name, option in stream.options.items():
                # If we find an option in the template that fits the source stream, select the source stream option
                # If there are no corresponding option in the template stream, select the source stream option
                template_options = template.get_option_by_name(option_name)
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
                ctn.add_stream_pairs(((idx, stream), target_stream))
            else:
                print('No stream')

        return ctn


class StreamTemplateFactory(object):

    @staticmethod
    def get_stream_template(stream: Stream, *options) -> Union[VideoStreamTemplate,
                                                               AudioStreamTemplate,
                                                               SubtitleStreamTemplate]:
        if isinstance(stream, VideoStream):
            return VideoStreamTemplate(*options)
        elif isinstance(stream, AudioStream):
            return AudioStreamTemplate(*options)
        elif isinstance(stream, SubtitleStreamTemplate):
            return SubtitleStreamTemplate(*options)


class LinkedContainer(object):
    """
    Linked Container enable to link source streams and target streams, in pairs, so that they
    can be processed one pair at a time to determine the options necessary to encode the source stream
    into the target stream.
    """

    def __init__(self, target):
        self.fmt = target
        self._stream_pairs = list()
        self.target_stream_count = 0

    @property
    def stream_pairs(self):
        return self._stream_pairs

    def add_stream_pairs(self, pair: Tuple[tuple, Stream]):
        if len(pair[0]) != 2:
            raise Exception('Not acceptable')
        assert isinstance(pair[0][1], type(pair[1]))

        self._stream_pairs.append((pair[0], (self.target_stream_count, pair[1])))
        self.target_stream_count += 1

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
                disp_option = stream.get_option_by_type(Disposition)
                if disp_option:
                    thedisposition = disp_option.value
                    thedisposition['default'] = 1 if k == 0 else 0
                    stream.replace_options(Disposition(thedisposition))
                else:
                    stream.add_option(Disposition({'default': 1 if k == 0 else 0}))
                k += 1

    def remove_matching_stream_pairs(self, *streams: Union[AudioStream, VideoStream, SubtitleStream]):
        """
        Removes stream pairs whose target_stream matches any of the streams specified in *streams
        :param streams:  AudioStream, VideoStream or SubtitleStream
        :return: None
        """
        newpairs = self._stream_pairs[:]

        for pair in self._stream_pairs:
            (source_index, source_stream), (target_index, target_stream) = pair
            for filter in streams:
                if isinstance(target_stream, type(filter)) and target_stream != filter:
                    newpairs.remove(pair)
        p = []
        for idx, pair in enumerate(newpairs):
            p.append((pair[0], (idx, pair[1][1])))

        return p


class OptionBuilder(object):

    def __init__(self):
        pass

    def build_options(self, lctn: LinkedContainer, preferred_codec: dict, *encoders):

        for pair in lctn.stream_pairs:
            (source_idx, source_stream), (target_idx, target_stream) = pair
            log.debug(f'\nSource:, {source_stream}\nTarget:, {target_stream}')

            fmt = target_stream.get_option_by_type(Codec).value

            streamformat = StreamFormatFactory.get_format(fmt)

            enc = None

            if fmt in preferred_codec:
                enc = preferred_codec[fmt]

            for k, option in source_stream.options.items():
                if k in target_stream.options:
                    if target_stream.options[k] == option:
                        del target_stream.options[k]

            if source_stream == target_stream:
                encoder = streamformat.get_encoder('copy', *target_stream.options.values(), Map((0, source_idx)))
            else:
                encoder = streamformat.get_encoder(enc, *target_stream.options.values(), Map((0, source_idx)))

            for enco in encoders:
                if type(encoder) == type(enco):
                    encoder = enco

            print(encoder.parse(target_idx))


if __name__ == '__main__':
    encoder = CodecFactory.get_codec_by_name('vorbis')
    laptop = '/Users/Jon/Downloads/in/The.Polar.Express.(2004).1080p.BluRay.MULTI.x264-DiG8ALL.mkv'
    desktop = "/Users/jon/Downloads/Geostorm 2017 1080p FR EN X264 AC3-mHDgz.mkv"
    ctn = ContainerFactory.container_from_ffprobe(laptop,
                                                  '/usr/local/bin/ffmpeg', '/usr/local/bin/ffprobe')

    vst = StreamTemplateFactory.get_stream_template(ctn.video_streams[0], Codec('h264'), Codec('hevc'), Height('600'),
                                                    Width(1920), Channels(2), Bitrate(2000))

    ost = StreamTemplateFactory.get_stream_template(AudioStream(), Channels(8), Codec('ac3'))
    sst = StreamTemplateFactory.get_stream_template(SubtitleStream(), Codec('mov_text'))

    tctn = ContainerFactory.container_from_template(ctn, 'mp4', [vst, ost, sst])
    vs = VideoStream(Codec('Vorbis'))

    tctn.add_stream_pairs(((0, ctn.get_stream(0)), vs))
    tctn.fix_disposition()

    toto = AudioStream(Bsf('p'))

    tctn.remove_matching_stream_pairs(toto)

    ob = OptionBuilder()
    ob.build_options(tctn, {'aac': 'faac'})

    print('yeah')
