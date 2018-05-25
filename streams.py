# coding=utf-8
from converter.streaminfo import MediaStreamInfo
from typing import Type
import languagecode


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
                 codecs=list,
                 bitrate=0,
                 height=0,
                 width=0,
                 level=0,
                 pix_fmts=list(),
                 profiles=list()):

        self.codecs = codecs
        self.bitrate = bitrate
        self.height = height
        self.width = width
        self.level = level
        self.pix_fmts = pix_fmts
        self.profiles = profiles

    def conforms(self, stream: Type[MediaStreamInfo]):

        if not stream.codec:
            return False

        if self.codecs and stream.codec not in self.codecs:
            return False

        elif self.bitrate and stream.bitrate > self.bitrate:
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

        else:
            return True


class AudioStreamTemplate(StreamTemplate):

    def __init__(self,
                 codecs=list,
                 bitrate=0,
                 channels=0):
        self.codecs = codecs
        self.bitrate = bitrate
        self.channels = channels

    def conforms(self, stream: Type[MediaStreamInfo]):

        if not stream.codec:
            return False

        if not stream.codec in self.codecs:
            return False

        if self.bitrate and stream.bitrate > self.bitrate:
            return False

        if self.channels and stream.channels > self.channels:
            return False

        else:
            return True


class SubtitleStreamTemplate(StreamTemplate):

    def __init__(self,
                 codecs=list):

        self.codecs = codecs

    def conforms(self, stream: Type[MediaStreamInfo]):

        if not stream.codec:
            return False

        if stream.codec not in self.codecs:
            return False

        else:
            return True
