# coding=utf-8
import abc
from converter.avcodecs import CodecFactory
from converter.streamformats import StreamFormatFactory
from converter.ffmpeg import MediaInfo, MediaStreamInfo
import logging
import languagecode
import sys
import os
from typing import Union, Dict


class Streams(object):

    def __init__(self):
        self._videos_streams = []
        self._audio_streams = []
        self._subtitle_streams = []

    @property
    def video_streams(self):
        return self._videos_streams

    @property
    def audio_streams(self):
        return self._audio_streams

    @property
    def subtitle_streams(self):
        return self._subtitle_streams

    def add_video_stream(self, stream):
        self._videos_streams.append(stream)

    def add_audio_stream(self, stream):
        self._audio_streams.append(stream)

    def add_subtitle_stream(self, stream):
        self._subtitle_streams.append(stream)


class StreamProcessor(object):
    streamtype = ''

    def __init__(self, cfg, container):
        self.config = cfg
        self.container = container

    def getcopycodec(self):
        """Returns the copy codec"""
        return CodecFactory.get('copy', self.__class__.streamtype, self.cfg)

    def getnullcodec(self):
        """Returns the null codec"""
        return CodecFactory.get('null', self.__class__.streamtype, self.cfg)


class VideoStreamProcessor(StreamProcessor):

    streamtype = 'video'

    def __init__(self, cfg, container):
        super(VideoStreamProcessor, self).__init__(cfg=cfg, container=container)

    def override(self, sourcestream, targetstream):
        """
        Compares source and target codecs. If source codecs fits within target codec limits, returns copy codec,
        if not, returns a codec parameterised for conversion.
        :param sourcestream: MediaStreamInfo
        :param targetstream: codec
        :return: codec
        """
        stream = StreamFormatFactory.get(targetstream, self.config)

        if sourcestream.codec != codec.codec_name:
            return codec

        if 'bitrate' in codec.safeopts and sourcestream.bitrate > codec.safeopts.bitrate:
            return codec

        if 'width' in codec.safeopts and sourcestream.width > codec.safeopts.width:
            return codec

        if 'height' in codec.safeopts and sourcestream.height > codec.safeopts['height']:
            return codec

        if self.config[self.container].get('pix_fmts') and sourcestream.pix_fmt not in self.config.get('pix_fmts'):
            return codec

        return CodecFactory.getvideo('copy', self.config)


class AudioStreamProcessor(StreamProcessor):

    def __init__(self, cfg, container):
        super(AudioStreamProcessor, self).__init__(cfg=cfg, container=container)


class Stream(object):

    def __init__(self, streamformat, cfg, index=0):
        self.format = streamformat.name
        self.index = index

        for option in cfg['StreamFormats'][self.format]:
            setattr(self, option, cfg['StreamFormats'].get(option))

