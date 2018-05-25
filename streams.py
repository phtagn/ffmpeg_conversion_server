# coding=utf-8
from converter.streaminfo import MediaStreamInfo
from typing import Type
import languagecode
import logging

log = logging.getLogger(__name__)

class StreamTemplate(object):

    def conforms(self, stream: Type[MediaStreamInfo]):
        """
        Tests conformance of the MediaStreamInfo object to the template.
        If values are None or otherwise empty in the template, conformance is True.
        :param stream: MediaStreamInfo object
        :return: bool
        """
        pass


class VideoStreamTemplate(StreamTemplate):
    """
    Template for video streams.
    """
    def __init__(self,
                 codec=str,
                 bitrate=0,
                 height=0,
                 width=0,
                 level=0,
                 pix_fmts=list(),
                 profiles=list(),
                 sfilter=None):

        self.codec = codec
        self.bitrate = bitrate
        self.height = height
        self.width = width
        self.level = level
        self.pix_fmts = pix_fmts
        self.profiles = profiles
        self.filter = sfilter

    def conforms(self, stream: Type[MediaStreamInfo], mode: str ='override'):
        """
        Checks if the stream conforms to the template.
        :param stream: the MediaStreamInfo stream that needs to be checked agains the template
        :type stream: MediaStreamInfo
        :param mode: Only 2 modes are acceptable 'copy', which will only check against the accepted formats specified
        in the config file, and 'override', which will also check against the settings provided for the stream.
        :type mode: str
        :return: True / False
        :rtype: bool
        """

        if mode not in ['copy', 'override']:
            log.error(f'Selected mode {mode} not copy or override, defaulting to copy')
            mode = 'copy'

        if not stream.codec:
            return False

        if self.filter:
            return False

        if self.codec and stream.codec != self.codec:
            return False

        if mode == 'override':
            if self.bitrate and stream.bitrate and stream.bitrate > self.bitrate:
                return False

            elif self.height and stream.height > self.height:
                return False

            elif self.width and stream.width > self.width:
                return False

            elif self.level and stream.level > self.level:
                return False

            elif self.pix_fmts and stream.pix_fmt not in self.pix_fmts:
                return False

            elif self.profiles and stream.profile not in self.profiles:
                return False

        return True


class AudioStreamTemplate(StreamTemplate):

    def __init__(self,
                 codec=str,
                 bitrate=0,
                 channels=0,
                 sfilter=None):

        self.codec = codec
        self.bitrate = bitrate
        self.channels = channels
        self.filter = sfilter

    def conforms(self, stream: Type[MediaStreamInfo]):

        if not stream.codec:
            return False

        if stream.codec != self.codecs:
            return False

        if self.bitrate and stream.bitrate > self.bitrate:
            return False

        if self.channels and stream.channels > self.channels:
            return False

        else:
            return True


class SubtitleStreamTemplate(StreamTemplate):

    def __init__(self,
                 codec=str):

        self.codec = codec

    def conforms(self, stream: Type[MediaStreamInfo]):

        if not stream.codec:
            return False

        if stream.codec != self.codec:
            return False

        else:
            return True
