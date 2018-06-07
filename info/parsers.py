import json
import locale
import logging
import languagecode
import abc
from abc import ABCMeta
from typing import Type, Union

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
console_encoding = locale.getdefaultlocale()[1] or 'UTF-8'


class IParser(metaclass=ABCMeta):
    """
    Parser Interface. The role of this class is to supply values that are usable by the program
    Most properties are self explanatory and have type hinting, but some of them have further comments.
    """

    def __init__(self, output):
        pass

    @abc.abstractmethod
    def nb_of_streams(self) -> int:
        pass

    @abc.abstractmethod
    def pix_fmt(self, index: Union[int, str]) -> str:
        pass

    @abc.abstractmethod
    def bitrate(self, index: Union[int, str]) -> int:
        """
        Bitrate should be expressed as an int representing thousands of bits, e.g. 384, not 384000
        """
        pass

    @abc.abstractmethod
    def codec(self, index: Union[int, str]) -> str:
        pass

    @abc.abstractmethod
    def duration(self, index: Union[int, str]):
        pass

    @abc.abstractmethod
    def width(self, index: Union[int, str]) -> int:
        pass

    @abc.abstractmethod
    def height(self, index: Union[int, str]) -> int:
        pass

    @abc.abstractmethod
    def language(self, index: Union[int, str]) -> str:
        pass

    @abc.abstractmethod
    def disposition(self, index: Union[int, str]) -> dict:
        pass

    @abc.abstractmethod
    def fps(self, index: Union[int, str]) -> int:
        pass

    @abc.abstractmethod
    def level(self, index: Union[int, str]) -> float:
        """
        Some programs indicate level as an int by multiplying it by 10. In this case the value should be divided
        by 10 here. E.g. level should be 4.1, not 41.
        """
        pass

    @abc.abstractmethod
    def profile(self, index: Union[int, str]) -> str:
        pass

    @abc.abstractmethod
    def channels(self, index: Union[int, str]) -> int:
        pass

    @abc.abstractmethod
    def samplerate(self, index: Union[int, str]) -> int:
        pass

    @abc.abstractmethod
    def codec_type(self, index: Union[int, str]) -> int:
        pass


class FFprobeParser(object):

    def __init__(self, jsonoutput):
        output = json.loads(jsonoutput)

        super(FFprobeParser, self).__init__()
        self.streams = output['streams']
        self.format = output['format']

    def nb_of_streams(self) -> int:
        return int(self.format.get('nb_streams', 0))

    def pix_fmt(self, index) -> str:
        return self.streams[index].get('pix_fmt', '')

    def bitrate(self, index) -> int:

        if self.streams[index].get('bit_rate', 0):
            br = int(self.streams[index]['bit_rate'])
        else:
            br = int(self.streams[index]['tags'].get('BPS', 0))

        return int(br/1000)

    def codec(self, index) -> str:
        return self.streams[index].get('codec_name', '')

    def channels(self, index) -> int:
        return self.streams[index].get('channels', 0)

    def duration(self, index):
        return 'toto'

    def height(self, index) -> int:
        return self.streams[index].get('height', 0)

    def width(self, index) -> int:
        return self.streams[index].get('width', 0)

    def language(self, index):
        return languagecode.validate(self.streams[index]['tags'].get('language', 'und'))

    def disposition(self, index) -> dict:
        return self.streams[index].get('disposition', {})

    def fps(self, index):
        return self.streams[index].get('r_frame_rate', '')

    def level(self, index):
        return float(self.streams[index].get('level', 0.0)) / 10

    def profile(self, index):
        return self.streams[index].get('profile', '')

    def samplerate(self, index):
        return int(self.streams[index].get('saloke_rate', 0))

    def codec_type(self, index: Union[int, str]) -> Union[str, None]:
        return self.streams[index].get('codec_type', None)



class ParserFactory(object):

    @staticmethod
    def get(parser: str, output) -> IParser:
        if parser == 'ffprobe':
            return FFprobeParser(output)
        else:
            raise UnsupportedParser

class UnsupportedParser(Exception):
    pass

