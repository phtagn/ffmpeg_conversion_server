import languagecode
import logging
from abc import abstractmethod, ABCMeta
from typing import Union

log = logging.getLogger(__name__)


class IStreamOption(metaclass=ABCMeta):
    name = ''
    ffprobe_name = ''
    """Interface for options that apply to streams. The constructor builds the stream specifier"""

    @abstractmethod
    def parse(self, stream_type: str, stream_number: Union[None, int] = None) -> list:
        """Returns the list of options to pass ffmpeg"""
        if stream_type == 'a' or stream_type == 'audio':
            self.stream_specifier = 'a'

        elif stream_type == 'v' or stream_type == 'video':
            self.stream_specifier = 'v'

        elif stream_type == 's' or stream_type == 'subtitle':
            self.stream_specifier = 's'

        else:
            log.exception('Streamtype %s was not one of a, v, s or audio, video, subtitle', stream_type)
            raise UnsupportedStreamType

        if stream_number is not None:
            self.stream_specifier = f'{self.stream_specifier}:{stream_number}'

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        if self.value == other.value:
            return True
        return False

    def __copy__(self):
        return type(self)(self.value)


class IStreamValueOption(IStreamOption):

    @abstractmethod
    def parse(self, stream_type: str, stream_number: Union[None, int] = None) -> list:
        super(IStreamValueOption, self).parse(stream_type, stream_number)

    def __lt__(self, other):
        if not isinstance(other, type(self)):
            return False
        if self.value < other.value:
            return True
        return False

    def __gt__(self, other):
        if not isinstance(other, type(self)):
            return False
        if self.value > other.value:
            return True
        return False

    def __le__(self, other):
        if not isinstance(other, type(self)):
            return False
        if self.value <= other.value:
            return True
        return False

    def __ge__(self, other):
        if not isinstance(other, type(self)):
            return False
        if self.value >= other.value:
            return True
        return False


class OptionFactory(object):
    options = {}

    @classmethod
    def get_option(cls, name):

        if name in cls.options:
            return cls.options[name]
        else:
            raise UnsupportedOption

    @classmethod
    def get_option_from_ffprobe(cls, ffprobe_name):
        ffprobe_dict = {option.ffprobe_name: option for option in cls.options.values()}
        if ffprobe_name in ffprobe_dict:
            return ffprobe_dict[ffprobe_name]
        else:
            return None

    @classmethod
    def register_option(cls, option):
        assert issubclass(option, IStreamOption)
        cls.options.update({option.name: option})

    @classmethod
    def get_option_by_type(cls, opt):
        this_module = __import__(__name__)
        option_class = getattr(this_module, str(opt.__name__))

        return option_class


class Codec(IStreamOption):
    name = 'codec'
    ffprobe_name = 'codec_name'

    def __init__(self, val: str):
        """

        :param val: name of the codec
        """
        self.value = val

    def parse(self, stream_type: str, stream_number: Union[None, int] = None) -> list:
        super(Codec, self).parse(stream_type, stream_number)
        return [f'-codec:{self.stream_specifier}', self.value]


OptionFactory.register_option(Codec)


class Map(IStreamValueOption):

    def __init__(self, val: tuple):
        if len(val) > 2:
            raise ValueError('Tuple can only contain 2 ints')
        if not isinstance(val[0], int) or not isinstance(val[1], int):
            raise Exception

        self.value = val

    def parse(self, stream_type: str, stream_number: Union[None, int] = None):
        return ['-map', f'{self.value[0]}:{self.value[1]}']


class Channels(IStreamValueOption):
    """Audio channel option (i.e. mono, stereo...)"""
    name = 'channels'
    ffprobe_name = 'channels'

    def __init__(self, val: int):
        """

        :param val: number of audio channels, from 1 to 12
        """
        assert isinstance(val, int)

        if val > 12:
            self.value = 12
        elif val < 1:
            self.value = 1
        else:
            self.value = val

    def parse(self, stream_type: str, stream_number: Union[None, int] = None) -> list:
        super(Channels, self).parse(stream_type, stream_number)

        return [f'-ac:{self.stream_specifier}', str(self.value)]


OptionFactory.register_option(Channels)


class Language(IStreamOption):
    """Language option, applies to audio and subtitle streams"""
    name = 'language'
    ffprobe_name = 'language'

    def __init__(self, val: str):
        """

        :param val: 3-letter language code
        """
        self.value = languagecode.validate(val)

    def parse(self, stream_type: str, stream_number: Union[None, int] = None) -> list:
        super(Language, self).parse(stream_type, stream_number)

        return [f'-metadata:s:{self.stream_specifier}', f'language={self.value}']


OptionFactory.register_option(Language)


class Bitrate(IStreamOption):
    """Bitrate option, applies to video and audio streams"""
    name = 'bitrate'
    ffprobe_name = ''

    def __init__(self, val: int):
        """

        :param val: bitrate, in thousands
        """
        assert isinstance(val, int)
        self.value = val

    def parse(self, stream_type: str, stream_number: Union[None, int] = None) -> list:
        super(Bitrate, self).parse(stream_type, stream_number)
        return [f'-b:{self.stream_specifier}', f'{self.value}k']

    def __lt__(self, other):
        if not isinstance(other, type(self)):
            return False
        if self.value < other.value:
            return True
        return False

    def __gt__(self, other):
        if not isinstance(other, type(self)):
            return False
        if self.value > other.value:
            return True
        return False

    def __le__(self, other):
        if not isinstance(other, type(self)):
            return False
        if self.value <= other.value:
            return True
        return False

    def __ge__(self, other):
        if not isinstance(other, type(self)):
            return False
        if self.value >= other.value:
            return True
        return False


OptionFactory.register_option(Bitrate)


class PixFmt(IStreamOption):
    """Pix_fmt option, applies to video streams"""
    name = 'pix_fmt'

    def __init__(self, val: str):
        """

        :param val: pix format see pix_fmt in ffmpeg documentation
        """
        assert isinstance(val, str)
        self.value = val

    def parse(self, stream_type: str, stream_number: Union[None, int] = None) -> list:
        super(PixFmt, self).parse(stream_type, stream_number)
        return [f'-pix_fmt:{self.stream_specifier}', str(self.value)]


OptionFactory.register_option(PixFmt)


class Bsf(IStreamOption):
    """Bitstream filter option
    Set bitstream filters for matching streams. bitstream_filters is a comma-separated list of bitstream filters."""
    name = 'bsf'

    def __init__(self, val: Union[list, str]):
        assert isinstance(val, (list, str))
        if isinstance(val, str):
            self.value = [val]
        else:
            self.value = val

    def parse(self, stream_type: str, stream_number: Union[None, int] = None) -> list:
        super(Bsf, self).parse(stream_type, stream_number)
        return [f'-bsf:{self.stream_specifier}', ','.join(self.value)]


OptionFactory.register_option(Bsf)


class Disposition(IStreamOption):
    """Sets the disposition for a stream.
    This option overrides the disposition copied from the input stream. It is also possible to delete the disposition by setting it to 0.
    The following dispositions are recognized:
    default, dub, original, comment, lyrics, karaoke, forced, hearing_impaired, visual_impaired, clean_effects
    attached_pic, captions, descriptions, dependent, metadata"""
    name = 'disposition'

    def __init__(self, val: dict):
        self.value = {}
        for k in val:
            if k.lower() not in ['default', 'dub', 'original', 'comment', 'lyrics', 'karaoke', 'forced',
                                 'hearing_impaired', 'visual_impaired', 'clean_effects', 'attached_pic', 'captions',
                                 'descriptions', 'dependent', 'metadata']:
                continue
            else:
                if val[k]:
                    self.value.update({k: val[k]})

    def parse(self, stream_type: str, stream_number: Union[None, int] = None) -> list:
        r = []
        super(Disposition, self).parse(stream_type, stream_number)
        for k, v in self.value:
            r.extend([f'-disposition:{self.stream_specifier}', k])
        return r

    def __eq__(self, other):
        if isinstance(other, Disposition):
            if self.value == other.value:
                return True

        return False

    def __ne__(self, other):
        if isinstance(other, Disposition):
            if self.value == other.value:
                return False

        return True


OptionFactory.register_option(Disposition)


class Height(IStreamValueOption):
    name = 'height'

    def __init__(self, val):
        if str(val).isnumeric():
            val = int(val)
        else:
            raise TypeError('Value for height should be numeric')
        self.value = val

    def parse(self, stream_type: str, stream_number: Union[None, int] = None) -> list:
        return []


class Width(IStreamValueOption):
    name = 'width'

    def __init__(self, val):
        if not str(val).isnumeric():
            raise TypeError('Value for width should be numeric')
        self.value = int(val)

    def parse(self, stream_type: str, stream_number: Union[None, int] = None) -> list:
        return []


class Level(IStreamValueOption):
    name = 'level'

    def __init__(self, val):
        try:
            self.value = float(val)
        except:
            raise TypeError('Value for level should be decimal')

    def parse(self, stream_type: str, stream_number: Union[None, int] = None) -> list:
        super(Level, self).parse(stream_type, stream_number)
        return [f'-level:{self.stream_specifier}', f'{self.value:.{1}}']


class Profile(IStreamOption):
    name = 'profile'

    def __init__(self, val):
        self.value = val

    def parse(self, stream_type: str, stream_number: Union[None, int] = None) -> list:
        super(Profile, self).parse(stream_type, stream_number)
        return [f'-profile:{self.stream_specifier}', str(self.value)]


class Filter(IStreamOption):

    def __init__(self, *filters):
        self._filters = []
        self.add_filter()

    def add_filter(self, *filters):
        for f in filters:
            if isinstance(f, Filters):
                self._filters.append(f)

    @property
    def filters(self):
        return self._filters

    def parse(self, stream_type: str, stream_number: Union[None, int] = None):
        super(Filter, self).parse(stream_type, stream_number)
        values = [f.filter for f in self.filters]
        print(';'.join(values))
        return [F'-filter:{self.stream_specifier}', ';'.join(values)]


class Filters:
    pass


class Scale(Filters):
    name = 'scale'

    def __init__(self, val: tuple):
        """
        Val is a tuple of height and width, see https://ffmpeg.org/ffmpeg-filters.html#scale-1
        :param val: tuple (width, height)
        :type val: tuple(int, int)
        """
        if len(val) != 2:
            raise Exception('Scale filter expects a tuple of width and height')
        self.w = val[0]
        self.h = val[1]

    @property
    def filter(self):
        return f'scale=w={self.w}:h={self.h}'


class Deblock(Filters):

    def __init__(self, **kwargs):
        k = list(zip(kwargs.keys(), kwargs.values()))
        a = []
        for t in k:
            a.append('='.join([str(t[0]), str(t[1])]))

        self.value = ':'.join(a)

    @property
    def filter(self):
        return f'deblock={self.value}'


class UnsupportedStreamType(Exception):
    pass


class UnsupportedOption(Exception):
    pass


if __name__ == '__main__':
    import converter.streams as streams

    filters = Filter()
    f = Scale((720, 400))
    d = Deblock(filter='weak', block=4, alpha=0.12, beta=0.07)
    filters.add_filter(d)
    filters.add_filter(f)
    print(filters.parse('v', 0))

    toto = OptionFactory.get_option_by_type(Codec)
    toto('ac3')

    of = OptionFactory()
    myoptr = of.get_option('bitrate')

    astream = streams.AudioStream(codec='toto',
                                  channels=Channels('a', 2),
                                  bitrate=Bitrate('a', 1500),
                                  language=Language('s', 'fre'),
                                  disposition={})
    bsf = Bsf('a', ['toto', 'tata'])
    print(bsf.parse())
    print(astream.channels.parse(), astream.bitrate.parse(), astream.language.parse())
    print('yeah')
