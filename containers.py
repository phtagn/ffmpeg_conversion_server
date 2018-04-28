# coding=utf-8
import abc
import logging
import os
import sys
from logging.config import fileConfig

import settings
from converter import ffmpeg


class GenericContainer(object):
    __metaclass__ = abc.ABCMeta

    videocodecs = []
    audiocodecs = []
    subtitlecodecs = []
    extensions = []
    format = ''
    badcodecs = []

    @abc.abstractmethod
    def generateaudiooptions(self):
        pass

    @abc.abstractmethod
    def generatevideooptions(self):
        pass

    @abc.abstractmethod
    def generatesubtitleoptions(self):
        pass

    def generatepreopts(self):
        options = []
        if self.settings.preopts:
            options.extend(self.settings.preopts)
        if self.subtitleoptions:
            options.append('-fix_sub_duration')

        return options

    def generatepostopts(self):
        options = []

        options.extend(['-threads', self.settings.threads])

        if self.settings.postopts:
            options.extend(self.settings.postopts)

        # HEVC Tagging for copied streams

        if self.fileinfo.video.codec.lower() in ['x265', 'h265', 'hevc']:
            options.extend(['-tag:v', 'hvc1'])
            self.log.info("Tagging copied video stream as hvc1")

        return options

    @classmethod
    def supports(cls, audio='', video='', subtitle=''):
        if audio in cls.audiocodecs or cls.audiocodecs[0] == '*':
            return True
        if video in cls.audiocodecs or cls.videocodecs[0] == '*':
            return True
        if subtitle in cls.subtitlecodecs or cls.subtitlecodecs[0] == '*':
            return True
        return False

    @staticmethod
    def estimateVideoBitrate(fileinfo: ffmpeg.MediaInfo):
        total_bitrate = fileinfo.format.bitrate
        audio_bitrate = 0

        for a in fileinfo.audio:
            audio_bitrate += a.bitrate

        # log.debug("Total bitrate is %s." % fileinfo.format.bitrate)
        # log.debug("Total audio bitrate is %s." % audio_bitrate)
        # log.debug("Estimated video bitrate is %s." % (total_bitrate - audio_bitrate))
        return ((total_bitrate - audio_bitrate) / 1000) * .95


class Container(object):
    supportedvideocodecs = []
    supportedautiocodecs = []
    supportedsubtitlecodecs = []
    extensions = []

    @classmethod
    def supports(cls, audio='', video='', subtitle=''):
        if audio in cls.supportedautiocodecs or cls.supportedautiocodecs[0] == '*':
            return True
        if video in cls.supportedvideocodecs or cls.supportedvideocodecs[0] == '*':
            return True
        if subtitle in cls.supportedsubtitlecodecs or cls.supportedsubtitlecodecs[0] == '*':
            return True
        return False


class MP4(GenericContainer):
    extensions = ['mp4', 'm4v']
    videocodecs = ['h264', 'h265', 'x264', 'x265']
    audiocodecs = ['aac', 'ac3', 'mp3', 'wma', 'opus']
    subtitlecodecs = ['mov_text']
    badcodecs = []
    format = 'mp4'

    def __init__(self, params, fileinfo, logger=None):
        self.settings = settings.SettingsManager().getsettings('default').MP4
        self.fileinfo = fileinfo
        if logger:
            self.log = logger
        else:
            fileConfig(os.path.join(os.path.dirname(sys.argv[0]), 'logging.ini'),
                       defaults={'logfilename': os.path.join(os.path.dirname(sys.argv[0]), 'server.log')})
            self.log = logging.getLogger(__name__)

    def validatesettings(self):
        for vcodec in self.settings.video_codec:
            if vcodec not in self.__class__.videocodecs:
                # log.info(f'Specified codec {vcodec} not supported by MP4 container, removing from list')
                self.settings.video_codec.remove(vcodec)
        if self.settings.preferred_video_codec not in self.__class__.videocodecs:
            # log.info(f'Preferred codec {self.settings.preferred_video_codec} not supported by MP4 container, replacing with h264')
            self.settings.preferred_video_codec = 'h264'  # TODO: find a better way to handle this

    def generatevideooptions(self):
        self.log.info("Reading video stream.")
        self.log.info("Video codec detected: %s." % self.fileinfo.video.codec)
        info = self.fileinfo.video
        vbr = None

        # try:
        #    vbr = self.estimateVideoBitrate()
        # except:
        #    vbr = self.fileinfo.format.bitrate / 1000

        if (info.codec.lower() in self.settings.video_codec):
            vcodec = 'copy'
        else:
            vcodec = self.settings.preferred_video_codec

        vbitrate = self.settings.video_bitrate if self.settings.video_bitrate else vbr

        self.log.info("Pix Fmt: %s." % info.pix_fmt)
        if self.settings.pix_fmt and info.pix_fmt.lower() not in self.settings.pix_fmt:
            self.log.debug("Overriding video pix_fmt. Codec cannot be copied because pix_fmt is not approved.")
            vcodec = self.settings.preferred_video_codec
            pix_fmt = self.settings.pix_fmt

            if self.settings.video_profile:
                vprofile = self.settings.video_profile
        else:
            pix_fmt = None

        if self.settings.video_bitrate and vbr > self.settings.video_bitrate:
            self.log.debug("Overriding video bitrate. Codec cannot be copied because video bitrate is too high.")
            vcodec = self.settings.preferred_video_codec
            vbitrate = self.settings.video_bitrate

        if self.settings.video_max_width and self.settings.video_max_width < info.video_width:
            self.log.debug(
                "Video width is over the max width, it will be downsampled. Video stream can no longer be copied.")
            vcodec = self.settings.preferred_video_codec
            vwidth = self.settings.video_max_width
        else:
            vwidth = None

        vlevel = info.video_level / 10
        if '264' in info.codec.lower() and self.settings.h264_max_level and info.video_level and (
                info.video_level / 10 > self.settings.h264_max_level):
            self.log.info("Video level %0.1f." % (info.video_level / 10))
            vcodec = self.settings.preferred_video_codec
            vlevel = 'aa'  # TODO : START HERE

        self.log.debug("Video codec: %s." % vcodec)
        self.log.debug("Video bitrate: %s." % vbitrate)
        self.log.info("Profile: %s." % info.profile)

        # TODO handle profiles for h264 and h265
        if self.settings.video_profile and info.profile.lower().replace(" ", "") not in self.settings.video_profile:
            self.log.debug("Video profile is not supported. Video stream can no longer be copied.")
            vcodec = self.settings.video_codec[0]
            vprofile = self.settings.video_profile[0]
            if self.settings.pix_fmt:
                pix_fmt = self.settings.pix_fmt
        else:
            vprofile = None

        options = {
            'codec': vcodec,
            'map': info.index,
            'bitrate': vbitrate,
            'level': self.settings.h264_level,
            'profile': vprofile,
            'pix_fmt': pix_fmt
        }

        if self.settings.video_crf:
            del options['video']['bitrate']
            options['video']['crf'] = self.settings.video_crf

        # Add width option
        if vwidth:
            options['video']['width'] = vwidth

        return options

    def generateaudiooptions(self):
        # Audio streams
        self.log.info("Reading audio streams.")

        overrideLang = True
        for a in self.fileinfo.audio:
            try:
                a.metadata['language'] = languagecode.validateLangCode(a.metadata['language'])
            except KeyError:
                a.metadata['language'] = 'und'

            if (a.metadata['language'] == 'und' and self.settings.adl != 'und') or (
                    self.settings.awl != 'und' and a.metadata['language'] in self.settings.awl):
                overrideLang = False
                break

        if overrideLang:
            self.settings.awl = 'und'
            self.log.info(
                "No audio streams detected in any appropriate language, relaxing restrictions so there will be some audio stream present.")

        audio_settings = {}
        l = 0
        for a in self.fileinfo.audio:
            try:
                a.metadata['language'] = languagecode.validateLangCode(a.metadata['language'])
            except KeyError:
                a.metadata['language'] = 'und'

            self.log.info("Audio detected for stream #%s: %s [%s]." % (a.index, a.codec, a.metadata['language']))

            if a.codec.lower() == 'truehd':  # Need to skip it early so that it flags the next track as default.
                self.log.info(
                    "MP4 containers do not support truehd audio, and converting it is inconsistent due to video/audio sync issues. Skipping stream %s as typically the 2nd audio track is the AC3 core of the truehd stream." % a.index)
                continue

            # Set undefined language to default language if specified
            if self.settings.adl != 'und' and a.metadata['language'] == 'und':
                self.log.debug("Undefined language detected, defaulting to [%s]." % self.settings.adl)
                a.metadata['language'] = self.settings.adl

            # Proceed if no whitelist is set, or if the language is in the whitelist
            iosdata = None
            if self.settings.awl == 'und' or a.metadata['language'] in self.settings.awl:
                # Create iOS friendly audio stream if the default audio stream has too many channels (iOS only likes AAC stereo)
                if self.settings.iOS and a.audio_channels > 2:
                    iOSbitrate = 256 if (self.settings.abitrate * 2) > 256 else (self.settings.abitrate * 2)
                    self.log.info(
                        "Creating audio stream %s from source audio stream %s [iOS-audio]." % (str(l), a.index))
                    self.log.debug("Audio codec: %s." % self.settings.iOS[0])
                    self.log.debug("Channels: 2.")
                    self.log.debug("Filter: %s." % self.settings.iOSfilter)
                    self.log.debug("Bitrate: %s." % iOSbitrate)
                    self.log.debug("Language: %s." % a.metadata['language'])
                    if l == 0:
                        disposition = 'default'
                        self.log.info("Audio track is number %s setting disposition to %s" % (str(l), disposition))
                    else:
                        disposition = 'none'
                        self.log.info("Audio track is number %s setting disposition to %s" % (str(l), disposition))
                    iosdata = {
                        'map': a.index,
                        'codec': self.settings.iOS[0],
                        'channels': 2,
                        'bitrate': iOSbitrate,
                        'filter': self.settings.iOSfilter,
                        'language': a.metadata['language'],
                        'disposition': disposition,
                    }
                    if not self.settings.iOSLast:
                        audio_settings.update({l: iosdata})
                        l += 1
                # If the iOS audio option is enabled and the source audio channel is only stereo, the additional iOS channel will be skipped and a single AAC 2.0 channel will be made regardless of codec preference to avoid multiple stereo channels
                self.log.info("Creating audio stream %s from source stream %s." % (str(l), a.index))

                if self.settings.iOS and a.audio_channels <= 2:
                    self.log.debug(
                        "Overriding default channel settings because iOS audio is enabled but the source is stereo [iOS-audio].")
                    acodec = 'copy' if a.codec in self.settings.iOS else self.settings.iOS[0]
                    audio_channels = a.audio_channels
                    afilter = self.settings.iOSfilter
                    abitrate = a.audio_channels * 128 if (a.audio_channels * self.settings.abitrate) > (
                            a.audio_channels * 128) else (a.audio_channels * self.settings.abitrate)
                else:
                    # If desired codec is the same as the source codec, copy to avoid quality loss
                    acodec = 'copy' if a.codec.lower() in self.settings.acodec else self.settings.acodec[0]
                    # Audio channel adjustments
                    if self.settings.maxchannels and a.audio_channels > self.settings.maxchannels:
                        audio_channels = self.settings.maxchannels
                        if acodec == 'copy':
                            acodec = self.settings.acodec[0]
                        abitrate = self.settings.maxchannels * self.settings.abitrate
                    else:
                        audio_channels = a.audio_channels
                        abitrate = a.audio_channels * self.settings.abitrate

                    # Bitrate calculations/overrides
                    if self.settings.abitrate is 0:
                        self.log.debug("Attempting to set bitrate based on source stream bitrate.")
                        try:
                            abitrate = a.bitrate / 1000
                        except:
                            self.log.warning(
                                "Unable to determine audio bitrate from source stream %s, defaulting to 256 per channel." % a.index)
                            abitrate = a.audio_channels * 256
                    afilter = self.settings.afilter

                self.log.debug("Audio codec: %s." % acodec)
                self.log.debug("Channels: %s." % audio_channels)
                self.log.debug("Bitrate: %s." % abitrate)
                self.log.debug("Language: %s" % a.metadata['language'])
                self.log.debug("Filter: %s" % afilter)

                # If the iOSFirst option is enabled, disable the iOS option after the first audio stream is processed
                if self.settings.iOS and self.settings.iOSFirst:
                    self.log.debug("Not creating any additional iOS audio streams.")
                    self.settings.iOS = False

                # Set first track as default disposition
                if l == 0:
                    disposition = 'default'
                    self.log.info("Audio Track is number %s setting disposition to %s" % (a.index, disposition))
                else:
                    disposition = 'none'
                    self.log.info("Audio Track is number %s setting disposition to %s" % (a.index, disposition))

                audio_settings.update({l: {
                    'map': a.index,
                    'codec': acodec,
                    'channels': audio_channels,
                    'bitrate': abitrate,
                    'filter': afilter,
                    'language': a.metadata['language'],
                    'disposition': disposition,
                }})

                if acodec == 'copy' and a.codec == 'aac' and self.settings.aac_adtstoasc:
                    audio_settings[l]['bsf'] = 'aac_adtstoasc'
                l += 1

                # Add the iOS track last instead
                if self.settings.iOSLast and iosdata:
                    iosdata['disposition'] = 'none'
                    audio_settings.update({l: iosdata})
                    l += 1

                if self.settings.audio_copyoriginal and acodec != 'copy':
                    self.log.info("Adding copy of original audio track in format %s" % a.codec)
                    audio_settings.update({l: {
                        'map': a.index,
                        'codec': 'copy',
                        'language': a.metadata['language'],
                        'disposition': 'none',
                    }})

        return audio_settings

    def generatepreopts(self):
        options = []
        if self.settings.preopts:
            options.extend(self.settings.preopts)
        if self.subtitleoptions:
            options.append('-fix_sub_duration')

        return options

    def generatepostopts(self):
        options = []

        options.extend(['-threads', self.settings.threads])

        if self.settings.postopts:
            options.extend(self.settings.postopts)

        # HEVC Tagging for copied streams

        if self.fileinfo.video.codec.lower() in ['x265', 'h265', 'hevc']:
            options.extend(['-tag:v', 'hvc1'])
            self.log.info("Tagging copied video stream as hvc1")

        return options

    def generatesubtitleoptions(self):
        return {}


"""
class mkvContainer(Container):
    extensions = ['mkv']
    supportedvideocodecs = ['*']
    supportedautiocodecs = ['*']
    supportedsubtitlecodecs = ['*']


class Containers(object):
    Containers = {}

    @classmethod
    def register(cls, container):
        for extension in container.extensions:
            cls.Containers[extension] = container

    @classmethod
    def getcontainer(cls, extension):
        if extension in cls.Containers.keys():
            return cls.Containers[extension]
        else:
            raise Exception(f'No such container {extension}.')


Containters.register(mp4Container)
Containters.register(mkvContainer)
"""
if __name__ == '__main__':
    import converter

    conv = converter.Converter('/usr/local/bin/ffmpeg', '/usr/local/bin/ffprobe')
    mkvinfo = conv.probe('/Users/Jon/Downloads/in/Fargo S02E01.mkv')
    test = MP4('defaults', mkvinfo)
    test.generatevideooptions()
    print(test.supports(video='truehd'))
