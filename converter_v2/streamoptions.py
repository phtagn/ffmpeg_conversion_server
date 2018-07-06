import languagecode
import logging
from abc import abstractmethod, ABCMeta
from typing import Union
from collections import Counter

log = logging.getLogger(__name__)


class IOption(metaclass=ABCMeta):

    @abstractmethod
    def __init__(self, value):
        self._value = value

    @abstractmethod
    def parse(self, *args, **kwargs) -> list:
        return []

    @property
    def value(self):
        if self._value:
            return self._value
        else:
            return None


class IStreamOption(IOption):
    name = ''
    ffprobe_name = ''
    incompatible_with = []

    """Interface for options that apply to streams. The constructor builds the stream specifier (e.g. a:0, v:1)."""

    @abstractmethod
    def __init__(self, value):
        super(IStreamOption, self).__init__(value)
        self.stream_specifier = None

    @abstractmethod
    def parse(self, stream_type: str, stream_number: Union[None, int] = None) -> list:
        """

        :param stream_type: str, the type of stream
        :param stream_number:
        :return:
        """
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

        return []

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return self.value == other.value

    def __copy__(self):
        return type(self)(self.value)

    def __str__(self):
        return f'{self.__class__.__name__}: {self.value}'

    def __hash__(self):
        return hash(self.value)


class MetadataOption(IOption):
    """Specific class for metadata options. Those need to be copied even if they are identical to the
    input options"""
    pass


class EncoderOption(IOption):
    """A specific type for options that are supported only by encoders. Streams (e.g. VideoStream...) will not accept
    those options."""
    pass


class IStreamValueOption(IStreamOption):
    """This is the class for options that support a numeric value. For those, lt, gt, ge, le, are supported
    on top of eq. A separate class is useful for the rest of the program to identify whether the option can support
    those operations."""

    @abstractmethod
    def parse(self, stream_type: str, stream_number: Union[None, int] = None):
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

        try:
            return cls.options[name.lower()]
        except KeyError:
            pass

        try:
            return cls.options[name]
        except KeyError:
            pass

        log.debug(f'Factory could not find option {name}. Is it supported ? Is it registered ?')
        return None

    @classmethod
    def register_option(cls, option):
        assert issubclass(option, IOption)
        cls.options.update({option.__name__: option})

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
        super(Codec, self).__init__(val)

    def parse(self, stream_type: str, stream_number: Union[None, int] = None) -> list:
        super(Codec, self).parse(stream_type, stream_number)
        return [f'-codec:{self.stream_specifier}', self.value]


OptionFactory.register_option(Codec)


class Fps(IStreamValueOption):

    def __init__(self, val: int):
        try:
            if val < 1 or val > 120:
                val = None
        except TypeError:
            val = None

        super(Fps, self).__init__(val)

    def parse(self, stream_type: str, stream_number: Union[None, int] = None):
        super(Fps, self).parse(stream_type, stream_number)
        return [f'-r:{self.stream_specifier}', str(self.value)]


OptionFactory.register_option(Fps)


class Map(IOption):
    """The map option."""

    def __init__(self, val: tuple):
        if len(val) > 2:
            raise ValueError('Tuple can only contain 2 ints')
        if not isinstance(val[0], int) or not isinstance(val[1], int):
            raise Exception

        super(Map, self).__init__(val)

    def parse(self, *args, **kwargs):
        return ['-map', f'{self.value[0]}:{self.value[1]}']


class Channels(IStreamValueOption):
    """Audio channel option (i.e. mono, stereo...)"""
    name = 'channels'
    ffprobe_name = 'channels'

    def __init__(self, val: int):
        """

        :param val: number of audio channels, from 1 to 12
        """
        try:
            if 13 < val or val < 0:
                val = None
        except TypeError:
            val = None

        super(Channels, self).__init__(val)

    def parse(self, stream_type: str, stream_number: Union[None, int] = None) -> list:
        super(Channels, self).parse(stream_type, stream_number)

        return [f'-ac:{self.stream_specifier}', str(self.value)]


OptionFactory.register_option(Channels)


class Language(MetadataOption):
    """Language option, applies to audio and subtitle streams"""
    name = 'language'
    ffprobe_name = 'language'
    must_copy = True

    def __init__(self, val: str):
        """

        :param val: 3-letter language code
        """
        val = languagecode.validate(val)
        super(Language, self).__init__(val)

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
        try:
            val = int(val)
        except ValueError:
            val = None

        super(Bitrate, self).__init__(val)

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


class Crf(EncoderOption):
    incompatible_with = [Bitrate]

    def __init__(self, val: int):
        try:
            if val > 51 or val < 0:
                val = None
        except TypeError:
            val = None

        super(Crf, self).__init__(val)

    def parse(self, stream_type: str, stream_number: Union[None, int] = None):
        super(Crf, self).parse(stream_type, stream_number)
        return [f'-crf:{self.stream_specifier}', str(self.value)]


OptionFactory.register_option(Crf)


class PixFmt(IStreamOption):
    """Pix_fmt option, applies to video streams"""
    name = 'pix_fmt'

    def __init__(self, val: str):
        """

        :param val: pix format see pix_fmt in ffmpeg documentation
        """
        super(PixFmt, self).__init__(val)

    def parse(self, stream_type: str, stream_number: Union[None, int] = None) -> list:
        super(PixFmt, self).parse(stream_type, stream_number)
        return [f'-pix_fmt:{self.stream_specifier}', str(self.value)]


OptionFactory.register_option(PixFmt)


class Bsf(EncoderOption):
    """Bitstream filter option
    Set bitstream filters for matching streams. bitstream_filters is a comma-separated list of bitstream filters."""
    name = 'bsf'

    def __init__(self, val: Union[list, str]):
        super(Bsf, self).__init__()
        if val:
            if isinstance(val, str):
                self.value = [val]
            elif isinstance(val, list):
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
        super(Disposition, self).__init__()
        self.value = {}
        for k in val:
            if k.lower() not in ['default', 'dub', 'original', 'comment', 'lyrics', 'karaoke', 'forced',
                                 'hearing_impaired', 'visual_impaired', 'clean_effects', 'attached_pic', 'captions',
                                 'descriptions', 'dependent', 'metadata']:
                continue
            else:
                self.value.update({k: val[k]})

    def parse(self, stream_type: str, stream_number: Union[None, int] = None) -> list:
        r = []
        super(Disposition, self).parse(stream_type, stream_number)
        for k, v in self.value.items():
            if v == 0:
                if k == 'default':
                    r.extend([f'-disposition:{self.stream_specifier}', 0])
            if v == 1:
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
        try:
            val = int(val)
        except ValueError:
            val = None
        super(Height, self).__init__(val)

    def parse(self, stream_type: str, stream_number: Union[None, int] = None) -> list:
        return []


OptionFactory.register_option(Height)


class Width(IStreamValueOption):
    name = 'width'

    def __init__(self, val):
        try:
            val = int(val)
        except ValueError:
            val = None

        super(Width, self).__init__(val)

    def parse(self, stream_type: str, stream_number: Union[None, int] = None) -> list:
        return []


OptionFactory.register_option(Width)


class Level(IStreamValueOption):
    name = 'level'

    def __init__(self, val):
        try:
            if float(val) > 0:
                val = float(val)
        except:
            pass

        super(Level, self).__init__(val)

    def parse(self, stream_type: str, stream_number: Union[None, int] = None) -> list:
        super(Level, self).parse(stream_type, stream_number)
        return [f'-level:{self.stream_specifier}', f'{self.value:{1}}']


OptionFactory.register_option(Level)


class Profile(IStreamOption):
    name = 'profile'

    def __init__(self, val):
        super(Profile, self).__init__(val)

    def parse(self, stream_type: str, stream_number: Union[None, int] = None) -> list:
        super(Profile, self).parse(stream_type, stream_number)
        return [f'-profile:{self.stream_specifier}', str(self.value)]


OptionFactory.register_option(Profile)


class Filter(IStreamOption):

    def __init__(self, *filters):
        super(Filter, self).__init__()
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


class UnsupportedStreamType(Exception):
    pass


class UnsupportedOption(Exception):
    pass


class Options(object):

    def __init__(self, allow_multiple=False):
        self._options = {}
        self.allow_multiple = allow_multiple

    @property
    def options(self):
        return self._options

    def add_options(self, *options):
        for opt in options:
            if issubclass(opt.__class__, IOption) and opt.value is not None:
                self._options.update({opt.__class__.__name__: opt})
            else:
                log.debug('Option %s was rejected because of None value', str(opt))

    def get_option(self, opt):
        if isinstance(opt, str):
            return self.options.get(opt, None)
        try:
            return self.options[opt.__name__]
        except AttributeError:
            pass
        try:
            return self.options[opt.__class__.__name__]
        except AttributeError:
            pass

        return None

    def __delitem__(self, key):
        option = self.get_option(key)
        if option:
            del self.options[option.__class__.__name__]

    def __iter__(self):
        for opt_name, opt_value in self.options.items():
            yield opt_name, opt_value

    def __eq__(self, other):
        return Counter(self.options) == Counter(other.options)


if __name__ == '__main__':
    a = Index(1)
    b = Index(3)
    print(a==b)


    c = Channels(2)
    b1 = Bitrate(512)
    b2 = Bitrate(512)
    print(b1 == c)
    o = Options()

    o.add_options(c, b2)
    print(b1 in o.options.values())

    del o[c]

    for k, v in o:
        print(f'{k} -- {v}')

    t = o[c]
    print('yeah')
