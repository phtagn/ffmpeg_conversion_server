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

    def __eq__(self, other):
        if not isinstance(other, Codec):
            return False
        if self.value == other.value:
            return True
        return False

OptionFactory.register_option(Codec)


class Channels(IStreamOption):
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

    def __eq__(self, other):
        if not isinstance(other, Channels):
            return False
        if self.value == other.value:
            return True
        return False


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

    def __eq__(self, other):
        if not isinstance(other, Language):
            return False
        elif self.value == other.value:
            return True
        else:
            return False


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

    def __eq__(self, other):
        if isinstance(other, Bitrate):
            if self.value == other.value:
                return True

        return False

    def __ne__(self, other):
        if isinstance(other, Bitrate):
            if self.value == other.value:
                return False

        return True


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

    def __eq__(self, other):
        if isinstance(other, PixFmt):
            if self.value == other.value:
                return True

        return False

    def __ne__(self, other):
        if isinstance(other, PixFmt):
            if self.value == other.value:
                return False

        return True


OptionFactory.register_option(PixFmt)


class Bsf(IStreamOption):
    """Bitstream filter option
    Set bitstream filters for matching streams. bitstream_filters is a comma-separated list of bitstream filters."""
    name = 'bsf'

    def __init__(self, stream_type: str, val: Union[list, str]):
        assert isinstance(val, (list, str))
        if isinstance(val, str):
            self.value = [val]
        else:
            self.value = val

    def parse(self, stream_type: str, stream_number: Union[None, int] = None) -> list:
        super(Bsf, self).parse(stream_type, stream_number)
        return [f'-bsf:{self.stream_specifier}', ','.join(self.value)]

    def __eq__(self, other):
        if isinstance(other, Bsf):
            if self.value == other.value:
                return True

        return False

    def __ne__(self, other):
        if isinstance(other, Bsf):
            if self.value == other.value:
                return False

        return True


OptionFactory.register_option(Bsf)


class Disposition(IStreamOption):
    """Sets the disposition for a stream.
    This option overrides the disposition copied from the input stream. It is also possible to delete the disposition by setting it to 0.
    The following dispositions are recognized:
    default, dub, original, comment, lyrics, karaoke, forced, hearing_impaired, visual_impaired, clean_effects
    attached_pic, captions, descriptions, dependent, metadata"""

    def __init__(self, val: dict):
        self.value = []
        for k in val:
            if k.lower() not in ['default', 'dub', 'original', 'comment', 'lyrics', 'karaoke', 'forced',
                                 'hearing_impaired', 'visual_impaired', 'clean_effects', 'attached_pic', 'captions',
                                 'descriptions', 'dependent', 'metadata']:
                continue
            else:
                if val[k]:
                    self.value.append(k)

    def parse(self, stream_type: str, stream_number: Union[None, int] = None) -> list:
        r = []
        super(Disposition, self).parse(stream_type, stream_number)
        for k in self.value:
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


class Height(IStreamOption):

    def __init__(self, val):
        self.value = val

    def parse(self, stream_type: str, stream_number: Union[None, int] = None) -> list:
        pass

    def __eq__(self, other):
        if isinstance(other, Height):
            if self.value == other.value:
                return True

        return False

    def __ne__(self, other):
        if isinstance(other, Height):
            if self.value == other.value:
                return False

        return True


class Width(IStreamOption):

    def __init__(self, val):
        self.value = val

    def parse(self, stream_type: str, stream_number: Union[None, int] = None) -> list:
        pass

    def __eq__(self, other):
        if isinstance(other, Width):
            if self.value == other.value:
                return True

        return False

    def __ne__(self, other):
        if isinstance(other, Width):
            if self.value == other.value:
                return False

        return True


class Level(IStreamOption):

    def __init__(self, val):
        self.value = val

    def parse(self, stream_type: str, stream_number: Union[None, int] = None) -> list:
        pass

    def __eq__(self, other):
        if isinstance(other, Level):
            if self.value == other.value:
                return True

        return False

    def __ne__(self, other):
        if isinstance(other, Level):
            if self.value == other.value:
                return False

        return True


class Profile(IStreamOption):

    def __init__(self, val):
        self.value = val

    def parse(self, stream_type: str, stream_number: Union[None, int] = None) -> list:
        pass

    def __eq__(self, other):
        if isinstance(other, Profile):
            if self.value == other.value:
                return True

        return False

    def __ne__(self, other):
        if isinstance(other, Profile):
            if self.value == other.value:
                return False

        return True


class UnsupportedStreamType(Exception):
    pass


class UnsupportedOption(Exception):
    pass


if __name__ == '__main__':
    import converter.streams as streams

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
