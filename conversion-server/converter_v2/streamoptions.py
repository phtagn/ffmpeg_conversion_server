from helpers import languagecode
import logging
from abc import abstractmethod, ABCMeta
from typing import Union
from inspect import isclass
from collections import Counter
from copy import copy

log = logging.getLogger(__name__)


class IStreamOption(metaclass=ABCMeta):
    name = ''
    ffprobe_name = ''
    incompatible_with = []

    """Interface for options that apply to streams. The constructor builds the stream specifier (e.g. a:0, v:1)."""

    def __init__(self):
        self.value = None
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
        return f'{self.__class__.__name__}: {str(self.value)}'

    def __hash__(self):
        return hash(self.value)


class MetadataOption(IStreamOption):
    """Specific class for metadata options. Those need to be copied even if they are identical to the
    input options"""


class EncoderOption(IStreamOption):
    """A specific type for options that are supported only by encoders. Streams (e.g. VideoStream...) will not accept
    those options."""


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

    #    @classmethod
    #    def get_option_from_ffprobe(cls, ffprobe_name):
    #        ffprobe_dict = {option.ffprobe_name: option for option in cls.options.values()}
    #        if ffprobe_name in ffprobe_dict:
    #            return ffprobe_dict[ffprobe_name]
    #        else:
    #            return None

    @classmethod
    def register_option(cls, option):
        assert issubclass(option, IStreamOption)
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
        super(Codec, self).__init__()
        """
        :param val: name of the codec
        """
        self.value = val

    def parse(self, stream_type: str, stream_number: Union[None, int] = None) -> list:
        super(Codec, self).parse(stream_type, stream_number)
        return [f'-codec:{self.stream_specifier}', self.value]


OptionFactory.register_option(Codec)


class Fps(IStreamValueOption):

    def __init__(self, val: int):
        super(Fps, self).__init__()
        if val > 1 or val < 120:
            self.value = val

    def parse(self, stream_type: str, stream_number: Union[None, int] = None):
        super(Fps, self).parse(stream_type, stream_number)
        return [f'-r:{self.stream_specifier}', str(self.value)]


OptionFactory.register_option(Fps)


class Map(IStreamValueOption):
    """The map option."""

    def __init__(self, val: tuple):
        super(Map, self).__init__()
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
        super(Channels, self).__init__()
        """

        :param val: number of audio channels, from 1 to 12
        """
        if str(val).isnumeric() and 13 > int(val) > 0:
            self.value = val

    def parse(self, stream_type: str, stream_number: Union[None, int] = None) -> list:
        super(Channels, self).parse(stream_type, stream_number)

        return [f'-ac:{self.stream_specifier}', str(self.value)]


OptionFactory.register_option(Channels)


class Language(MetadataOption):
    """Language option, applies to audio and subtitle streams"""
    name = 'language'
    ffprobe_name = 'language'

    def __init__(self, val: str):
        super(Language, self).__init__()
        """

        :param val: 3-letter language code
        """
        self.value = languagecode.validate(val)

    def parse(self, stream_type: str, stream_number: Union[None, int] = None) -> list:
        super(Language, self).parse(stream_type, stream_number)

        return [f'-metadata:s:{self.stream_specifier}', f'language={self.value}']

    def __eq__(self, other):
        if not isinstance(other, Language):
            return False

        if self.value == 'und' or other.value == 'und':
            return True
        else:
            return self.value == other.value


OptionFactory.register_option(Language)


class Tag(MetadataOption):
    name = 'tag'

    def __init__(self, val):
        super(Tag, self).__init__()
        self.value = val

    def parse(self, stream_type: str, stream_number: Union[None, int] = None) -> list:
        super(Tag, self).parse(stream_type, stream_number)
        return [f'-tag:{self.stream_specifier}', f'{self.value}']

OptionFactory.register_option(Tag)

class Bitrate(IStreamValueOption):
    """Bitrate option, applies to video and audio streams"""
    name = 'bitrate'
    ffprobe_name = ''

    def __init__(self, val: int):
        super(Bitrate, self).__init__()
        """

        :param val: bitrate, in thousands
        """
        if str(val).isnumeric():
            self.value = int(val)

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
        super(Crf, self).__init__()
        try:
            if 51 > val > 0:
                self.value = val
        except TypeError:
            pass

    def parse(self, stream_type: str, stream_number: Union[None, int] = None):
        super(Crf, self).parse(stream_type, stream_number)
        return [f'-crf:{self.stream_specifier}', str(self.value)]


OptionFactory.register_option(Crf)


class PixFmt(IStreamOption):
    """Pix_fmt option, applies to video streams"""
    name = 'pix_fmt'

    def __init__(self, val: str):
        super(PixFmt, self).__init__()
        """

        :param val: pix format see pix_fmt in ffmpeg documentation
        """
        self.value = val

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


class Disposition(MetadataOption):
    def __init__(self, val):
        super(Disposition, self).__init__()
        if 'default' in val:
            self.value = val['default']
        else:
            self.value = None

    def parse(self, stream_type: str, stream_number: Union[None, int] = None) -> list:
        super(Disposition, self).parse(stream_type, stream_number)
        return [f'-disposition:{self.stream_specifier}', str(self.value)]


class Disposition2(MetadataOption):
    """Sets the disposition for a stream.
    This option overrides the disposition copied from the input stream. It is also possible to delete the disposition by setting it to 0.
    The following dispositions are recognized:
    default, dub, original, comment, lyrics, karaoke, forced, hearing_impaired, visual_impaired, clean_effects
    attached_pic, captions, descriptions, dependent, metadata"""
    name = 'disposition'

    def __init__(self, val: dict):
        super(Disposition2, self).__init__()
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
        super(Height, self).__init__()
        try:
            val = None if val < 0 else val
        except TypeError:
            val = None

        self.value = val

    def parse(self, stream_type: str, stream_number: Union[None, int] = None) -> list:
        return []


OptionFactory.register_option(Height)


class Width(IStreamValueOption):
    name = 'width'

    def __init__(self, val):
        super(Width, self).__init__()
        try:
            val = None if val < 0 else val
        except TypeError:
            val = None

        self.value = val

    def parse(self, stream_type: str, stream_number: Union[None, int] = None) -> list:
        return []


OptionFactory.register_option(Width)


class Level(IStreamValueOption):
    name = 'level'

    def __init__(self, val):
        super(Level, self).__init__()
        try:
            if float(val) > 0:
                self.value = float(val)
        except:
            pass

    def parse(self, stream_type: str, stream_number: Union[None, int] = None) -> list:
        super(Level, self).parse(stream_type, stream_number)
        return [f'-level:{self.stream_specifier}', f'{self.value:{1}}']


OptionFactory.register_option(Level)


class Profile(IStreamOption):
    name = 'profile'

    def __init__(self, val):
        super(Profile, self).__init__()
        self.value = val

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


class Options(object):

    def __init__(self):
        self.options = []

    def add_option(self, opt, unique=False):

        if issubclass(opt.__class__, IStreamOption) and opt.value is not None:
            if not unique:
                self.options.append(opt)
            else:
                opts = [o for o in self.options if o.__class__ != opt.__class__]
                opts.append(opt)
                self.options = opts[:]
        else:
            pass
            # log.debug('Option %s was rejected because of None value', str(opt))

    def get_option(self, option):

        for opt in self.options:
            if opt.__class__ == option:
                yield opt

    def del_option(self, option):
        for opt in self.options:
            if opt.__class__ == option:
                self.options.remove(opt)

    def get_unique_option(self, option):
        for opt in self.options:
            if option == opt.__class__:
                return opt

    def has_option(self, opt):

        o = opt if isclass(opt) else opt.__class__

        if o in [option.__class__ for option in self.options]:
            return True
        return False

    def incompatible_options(self, other):
        if not isinstance(other, Options):
            return False

        incompatible_options = Options()

        for me_opt in self.options:
            default = None
            for o_opt in other.get_option(me_opt.__class__):
                default = o_opt if not default else default
                if isinstance(me_opt, IStreamValueOption):
                    if me_opt < o_opt:
                        default = None
                        break
                else:
                    if me_opt == o_opt:
                        default = None
                        break
            if default:
                incompatible_options.add_option(default)

        return incompatible_options

    def contains_subset(self, other):
        if not isinstance(other, Options):
            return False

        for opt in other.options:
            if not self.has_option(opt):
                continue
            else:
                if opt not in self.options:
                    return False

        return True

    def __eq__(self, other):
        return Counter(self.options) == Counter(other.options)

    def __iter__(self):
        for opt in self.options:
            yield opt

    def __copy__(self):
        new = type(self)()
        for opt in self.options:
            new.add_option(copy(opt))
        return new
