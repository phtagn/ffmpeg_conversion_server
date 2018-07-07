from typing import Union, List, Dict

from converter_v2.streamoptions import Codec, Options, IStreamOption
from converter_v2.streams import VideoStream, AudioStream, SubtitleStream, Stream
import logging

log = logging.getLogger(__name__)


class Templates(object):

    def __init__(self):
        self.options = {}
