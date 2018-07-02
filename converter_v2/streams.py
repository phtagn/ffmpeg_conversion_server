from converter_v2.encoders import *
from converter_v2.streamoptions import *
from converter_v2.streamformats import StreamFormatFactory
import logging
import copy

log = logging.getLogger(__name__)


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
        """Add options to the options pool. Reject options if they are not supported or if the value is None.
        """
        for opt in options:
            if type(opt) in self.supported_options and opt.value is not None:
                if opt.__class__.__name__ not in self._options:
                    self._options.update({opt.__class__.__name__: opt})
                    log.debug('Option %s added to %s', str(opt), opt.__class__.__name__)
                else:
                    log.warning('Option %s already present, not adding', opt.__class__.__name__)
            else:
                log.warning('Option %s was rejected because unsupported by %s or None', str(opt),
                            self.__class__.__name__)

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

    def get_option_by_type(self, option) -> Union[IStreamOption, None]:
        # assert isinstance(option, IStreamOption)
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
        if isinstance(stream, VideoStream):
            return VideoStream()
        elif isinstance(stream, AudioStream):
            return AudioStream()
        elif isinstance(stream, SubtitleStream):
            return SubtitleStream()


class VideoStream(Stream):
    supported_options = [Codec, PixFmt, Bitrate, Disposition, Height, Width, Level, Profile]


#    def __init__(self, *options):
#        super(VideoStream, self).__init__(*options)
# self.type = 'video'

#    def __copy__(self):
#        super(VideoStream, self).__copy__()


class AudioStream(Stream):
    supported_options = [Codec, Channels, Language, Disposition, Bitrate]


#    def __init__(self, *options):
#        super(AudioStream, self).__init__(*options)
# self.type = 'audio'

#    def __copy__(self):
#        super(AudioStream, self).__copy__()


class SubtitleStream(Stream):
    supported_options = [Codec, Language, Disposition]


#    def __init__(self, *options):
#        super(SubtitleStream, self).__init__(*options)
# self.type = 'subtitle'


class OptionBuilder(object):

    def __init__(self):
        pass

    def build_options(self, lctn, preferred_codec: dict, *encoders):
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

            if source_stream == target_stream:
                encoder = streamformat.get_encoder('copy', *target_stream.options.values(), Map((0, source_idx)))
            else:
                encoder = streamformat.get_encoder(enc, *target_stream.options.values(), Map((0, source_idx)))

            for enco in encoders:
                if type(encoder) == type(enco):
                    encoder.add_option(enco.options)

            opts.extend(encoder.parse(target_idx))

        return opts


if __name__ == '__main__':
    from converter_v2.templates import StreamTemplateFactory

    from converter_v2.containers import ContainerFactory

    encoder = CodecFactory.get_codec_by_name('vorbis')
    laptop = '/Users/Jon/Downloads/in/The.Polar.Express.(2004).1080p.BluRay.MULTI.x264-DiG8ALL.mkv'
    desktop = "/Users/jon/Downloads/Geostorm 2017 1080p FR EN X264 AC3-mHDgz.mkv"
    ctn = ContainerFactory.container_from_ffprobe(desktop,
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
