import json
import locale
from converter_v2.streamoptions import *

log = logging.getLogger(__name__)

console_encoding = locale.getdefaultlocale()[1] or 'UTF-8'


class FFprobeParser(object):

    def __init__(self, jsonoutput):
        output = json.loads(jsonoutput)
        self._streams = output['streams']
        self._format = output['format']


    @property
    def streams(self):
        return self._streams

    @property
    def format(self):
        return self._format['format_name'].lower()

    def pix_fmt(self, index) -> PixFmt:
        return PixFmt(self.streams[index].get('pix_fmt', ''))

    def bitrate(self, index) -> Bitrate:

        if self.streams[index].get('bit_rate', 0):
            br = int(self.streams[index]['bit_rate'])
        else:
            br = int(self.streams[index]['tags'].get('BPS', 0))

        return Bitrate(int(br/1000))

    def codec(self, index) -> Codec:
        return Codec(self.streams[index].get('codec_name', ''))

    def channels(self, index) -> Channels:
        return Channels(self.streams[index].get('channels', 0))

    def height(self, index) -> Height:
        return Height(self.streams[index].get('height', 0))

    def width(self, index) -> Width:
        return Width(self.streams[index].get('width', 0))

    def language(self, index):
        return Language(self.streams[index]['tags'].get('language', 'und'))

    def disposition(self, index) -> Disposition:
        return Disposition(self.streams[index].get('disposition', {}))

    def level(self, index) -> Level:
        return Level(float(self.streams[index].get('level', 0.0)) / 10)

    def profile(self, index) -> Profile:
        return Profile(self.streams[index].get('profile', ''))

    def codec_type(self, index: Union[int, str]) -> Union[str, None]:
        return self.streams[index].get('codec_type', None)
