import languagecode
import logging
from abc import abstractmethod, ABCMeta
from typing import Union

log = logging.getLogger(__name__)



class IStreamOption(metaclass=ABCMeta):
    name = ''
    ffprobe_name = ''
    """Interface for options that apply to streams. The constructor builds the stream specifier"""

    def __init__(self):
        self.value = None

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
        if self.value == other.value:
            return True
        return False

    def __copy__(self):
        return type(self)(self.value)

    def __str__(self):
        return f'{self.__class__.__name__}: {self.value}'


class OptionClassFactory(object):

    @staticmethod
    def get_istreamoption(name, argnames):
        option = type(name, (IStreamOption,), {'__init__': IStreamOption.__init__})
        return option


class IStreamValueOption(IStreamOption):

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


class EncoderOption(IStreamOption):
    pass


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

        log.debug(f'Option {name} is not supported')
        return None

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


class Crf(EncoderOption):

    def __init__(self, val: int):
        super(Crf, self).__init__()
        if 51 > val > 0:
            self.value = val

    def parse(self, stream_type: str, stream_number: Union[None, int] = None):
        super(Crf, self).parse(stream_type, stream_number)
        return [f'-crf:{self.stream_specifier}', str(self.value)]


OptionFactory.register_option(EncoderOption)


class Map(IStreamValueOption):

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


class Language(IStreamOption):
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


OptionFactory.register_option(Language)


class Bitrate(IStreamOption):
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
        super(Height, self).__init__()
        if str(val).isnumeric():
            self.value = val

    def parse(self, stream_type: str, stream_number: Union[None, int] = None) -> list:
        return []


OptionFactory.register_option(Height)


class Width(IStreamValueOption):
    name = 'width'

    def __init__(self, val):
        super(Width, self).__init__()
        if str(val).isnumeric():
            self.value = int(val)

    def parse(self, stream_type: str, stream_number: Union[None, int] = None) -> list:
        return []


OptionFactory.register_option(Width)


class Level(IStreamValueOption):
    name = 'level'

    def __init__(self, val):
        super(Level, self).__init__()
        try:
            self.value = float(val)
        except:
            pass

    def parse(self, stream_type: str, stream_number: Union[None, int] = None) -> list:
        super(Level, self).parse(stream_type, stream_number)
        return [f'-level:{self.stream_specifier}', f'{self.value:.{1}}']


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
