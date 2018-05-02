# coding=utf-8
import abc
import logging
import os
import sys
from logging.config import fileConfig
from typing import Union, Dict, List

import languagecode
from converter.avcodecs import audio_codec_dict, video_codec_dict, subtitle_codec_dict


class GenericContainer(object):
    __metaclass__ = abc.ABCMeta

    videocodecs = []
    audiocodecs = []
    subtitlecodecs = []
    extensions = []
    format = ''
    badcodecs = []  # Codecs that cannot be converted

    def __init__(self, params, mediainfo, logger=None):

        if logger:
            self.log = logger
        else:
            fileConfig(os.path.join(os.path.dirname(sys.argv[0]), 'logging.ini'),
                       defaults={'logfilename': os.path.join(os.path.dirname(sys.argv[0]), 'server.log')})
            self.log = logging.getLogger(__name__)

        self.log.setLevel(10)
        for codec in self.settings.video_codecs:
            if codec not in self.__class__.videocodecs or codec not in video_codec_dict:
                self.settings.video_codecs.remove(codec)

        for codec in self.settings.audio_codecs:
            if codec not in self.__class__.audiocodecs or codec not in audio_codec_dict:
                self.settings.audio_codecs.remove(codec)

        for codec in self.settings.subtitle_codecs:
            if codec not in self.__class__.subtitlecodecs and codec not in subtitle_codec_dict:
                self.settings.subtitle_codecs.remove(codec)

        if not self.settings.video_codecs:
            raise Exception(
                f'All video codecs listed in video_codecs are invalid. Select one from {self.__class__.videocodecs}')

        if not self.settings.audio_codecs:
            raise Exception(
                f'All video codecs listed in video_codecs are invalid. Select one from {self.__class__.audiocodecs}')

        if not self.settings.subtitle_codecs:
            raise Exception(
                f'All video codecs listed in video_codecs are invalid. Select one from {self.__class__.subtitlecodecs}')

        self.videooptions = self.generatevideooptions()
        self.audiooptions = self.generateaudiooptions()
        self.subtitleoptions = self.generatesubtitleoptions()

    @abc.abstractmethod
    def generateaudiooptions(self) -> Dict[str, Union[str, int]]:
        pass

    @abc.abstractmethod
    def generatevideooptions(self) -> Dict[str, Union[str, int]]:
        pass

    @abc.abstractmethod
    def generatesubtitleoptions(self, subtitles: List[str] = []) -> Dict[str, Union[str, int]]:
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

    def estimateVideoBitrate(self):
        total_bitrate = self.mediainfo.format.bitrate
        audio_bitrate = 0

        for a in self.mediainfo.audio:
            audio_bitrate += a.bitrate

        self.log.debug("Total bitrate is %s." % self.mediainfo.format.bitrate)
        self.log.debug("Total audio bitrate is %s." % audio_bitrate)
        self.log.debug("Estimated video bitrate is %s." % (total_bitrate - audio_bitrate))
        return ((total_bitrate - audio_bitrate) / 1000) * .95


class MP4(GenericContainer):
    extensions = ['mp4', 'm4v']
    videocodecs = ['h264', 'h265', 'x264', 'x265']
    audiocodecs = ['aac', 'ac3', 'mp3', 'wma', 'opus']
    subtitlecodecs = ['mov_text']
    badcodecs = ['truehd']
    format = 'mp4'
    name = 'mp4'

    def __init__(self, params, mediainfo, logger=None):
        """Handles initial loading of settings from settings manager as well as settings validation
        comparing them to both what's allowed in the container and the codec supported by the program"""

        self.settings = params
        self.mediainfo = mediainfo
        super(MP4, self).__init__(params, mediainfo, logger)


    def generatevideooptions(self):
        """Generates a dictionary with video options"""
        self.log.info("Reading video stream.")
        self.log.info("Video codec detected: %s." % self.mediainfo.video.codec)
        info = self.mediainfo.video
        vbr = None

        try:
            vbr = self.estimateVideoBitrate()
        except:
            vbr = self.fileinfo.format.bitrate / 1000

        if (info.codec.lower() in self.settings.video_codecs):
            vcodec = 'copy'
        else:
            vcodec = self.settings.video_codecs[0]

        vbitrate = self.settings.video_bitrate if self.settings.video_bitrate else vbr

        self.log.info("Pix Fmt: %s." % info.pix_fmt)
        if self.settings.pix_fmts and info.pix_fmt.lower() not in self.settings.pix_fmts:
            self.log.debug("Overriding video pix_fmt. Codec cannot be copied because pix_fmt is not approved.")
            vcodec = self.settings.video_codecs[0]
            pix_fmt = self.settings.pix_fmts[0]

            if self.settings.video_profiles:
                vprofile = self.settings.video_profiles[0]

        else:
            pix_fmt = None

        if self.settings.video_bitrate and vbr > self.settings.video_bitrate:
            self.log.debug("Overriding video bitrate. Codec cannot be copied because video bitrate is too high.")
            vcodec = self.settings.video_codecs[0]
            vbitrate = self.settings.video_bitrate

        if self.settings.video_max_width and self.settings.video_max_width < info.video_width:
            self.log.debug(
                "Video width is over the max width, it will be downsampled. Video stream can no longer be copied.")
            vcodec = self.settings.video_codecs[0]
            vwidth = self.settings.video_max_width
        else:
            vwidth = None

        vlevel = info.video_level / 10
        if '264' in info.codec.lower() and self.settings.h264_max_level and info.video_level and (
                info.video_level / 10 > self.settings.h264_max_level):
            self.log.info("Video level %0.1f." % (info.video_level / 10))
            vcodec = self.settings.video_codecs[0]
            vlevel = self.settings.h264_max_level

        self.log.debug("Video codec: %s." % vcodec)
        self.log.debug("Video bitrate: %s." % vbitrate)
        self.log.info("Profile: %s." % info.profile)

        # TODO handle profiles for h264 and h265
        if self.settings.video_profiles and info.profile.lower().replace(" ", "") not in self.settings.video_profiles:
            self.log.debug("Video profile is not supported. Video stream can no longer be copied.")
            vcodec = self.settings.video_codecs[0]
            vprofile = self.settings.video_profiles[0]
            if self.settings.pix_fmt:
                pix_fmt = self.settings.pix_fmts[0]
        else:
            vprofile = None

        options = {
            'codec': vcodec,
            'map': info.index,
            'bitrate': vbitrate,
            'level': vlevel,
            'profile': vprofile,
            'pix_fmt': pix_fmt
        }

        if self.settings.video_crf:
            del options['bitrate']
            options['crf'] = self.settings.video_crf

        # Add width option
        if vwidth:
            options['width'] = vwidth

        return options

    def selectlanguage(self, streams: list):
        """Take a list of audio or subtitle MediaStreamInfo objects and returns
        a sublist of audio or subtitle streams with suitable language"""
        output = []

        # TODO: this should go in settings validation
        self.settings.audio_languages = languagecode.validate(self.settings.audio_languages)
        self.settings.audio_default_language = languagecode.validate(self.settings.audio_default_language)

        for s in streams:
            if s.type == 'audio' or s.type == 'subtitle':
                try:
                    if s.metadata['language'].strip() == "" or s.metadata['language'] is None:
                        s.metadata['language'] = 'und'
                except KeyError:
                    s.metadata['language'] = 'und'
                if s.metadata['language'] in self.settings.audio_languages or (
                        self.settings.audio_languages[0] == 'und' and self.settings.audio_default_language == 'und'):
                    output.append(s)

        if not output:
            for s in streams:
                output.append(s)

        return output

    def generateaudiooptions(self):
        """Generates a dictionary with audio options"""
        # Audio streams
        self.log.info("Reading audio streams.")
        info = self.selectlanguage(self.mediainfo.audio)

        #        overrideLang = True
        #        for a in info:
        #            try:
        #                a.metadata['language'] = languagecode.validate(a.metadata['language'])
        #            except KeyError:
        #                a.metadata['language'] = 'und'

        #            if (a.metadata['language'] == 'und' and self.settings.audio_default_language != 'und') or (
        #                    self.settings.audio_languages[0] != 'und' and a.metadata['language'] in self.settings.audio_languages):
        #                overrideLang = False
        #                break

        #        if overrideLang:
        #            self.settings.audio_languages = ['und']
        #            self.log.info(
        #                'No audio streams detected in any appropriate language, relaxing restrictions so there will be some audio stream present.')


        audio_settings = {}
        l = 0
        for a in info:
            self.log.debug(f'Considering track {a.index}')
            # Weed out the codecs that we cannot convert from
            if a.codec.lower() in self.__class__.badcodecs:
                self.log.info(
                    f"MP4 containers do not support {a.codec.lower}, and converting does not work. Skipping stream {a.index}")
                continue

            # Select track if language matches audio_languages settings
            #            try:
            #                a.metadata['language'] = languagecode.validate(a.metadata['language'])
            #            except KeyError:
            #                a.metadata['language'] = 'und'

            self.log.info("Audio detected for stream #%s: %s [%s]." % (a.index, a.codec, a.metadata['language']))

            # In output, set undefined language to default language if specified
            #            if self.settings.audio_default_language and a.metadata['language'] == 'und':
            #                self.log.debug(f"Undefined language detected, defaulting to {self.settings.audio_default_language}.")
            #                a.metadata['language'] = self.settings.audio_default_language

            # Proceed if no whitelist is set, or if the language is in the whitelist
            iosdata = None
            if self.settings.audio_languages[0] == 'und' or a.metadata['language'] in self.settings.audio_languages:

                # Create iOS friendly audio stream if the default audio stream has too many channels (iOS only likes AAC stereo)
                if self.settings.ios_audio and a.audio_channels > 2:
                    iOSbitrate = 256 if (self.settings.audio_bitrate * 2) > 256 else (self.settings.audio_bitrate * 2)
                    self.log.info(
                        "Creating audio stream %s from source audio stream %s [iOS-audio]." % (str(l), a.index))

                    # Set dispostion of first track to avoid iOS playing several audio tracks at once
                    if l == 0:
                        disposition = 'default'
                        self.log.info("Audio track is number %s setting disposition to %s" % (str(l), disposition))
                    else:
                        disposition = 'none'
                        self.log.info("Audio track is number %s setting disposition to %s" % (str(l), disposition))
                    iosdata = {
                        'map': a.index,
                        'codec': 'aac',
                        'channels': 2,
                        'bitrate': iOSbitrate,
                        'filter': self.settings.ios_audio_filter,
                        'language': a.metadata['language'],
                        'disposition': disposition,
                    }
                    self.log.debug("Audio codec: aac")
                    self.log.debug("Channels: 2.")
                    self.log.debug("Filter: %s." % self.settings.ios_audio_filter)
                    self.log.debug("Bitrate: %s." % iOSbitrate)
                    self.log.debug("Language: %s." % a.metadata['language'])
                    self.log.debug("Disposition: %s." % disposition)

                    if not self.settings.ios_move_last:
                        audio_settings.update({l: iosdata})
                        l += 1

                # If the iOS audio option is enabled and the source audio channel is only stereo, the additional iOS channel will be skipped and a single AAC 2.0 channel will be made regardless of codec preference to avoid multiple stereo channels
                self.log.info("Creating audio stream %s from source stream %s." % (str(l), a.index))

                if self.settings.ios_audio and a.audio_channels <= 2:
                    self.log.debug(
                        "Overriding default channel settings because iOS audio is enabled but the source is stereo [iOS-audio].")
                    acodec = 'copy' if a.codec == 'aac' else 'aac'
                    audio_channels = a.audio_channels
                    afilter = self.settings.ios_audio_filter
                    abitrate = a.audio_channels * 128 if (a.audio_channels * self.settings.audio_bitrate) > (
                            a.audio_channels * 128) else (a.audio_channels * self.settings.audio_bitrate)
                else:
                    # If desired codec is the same as the source codec, copy to avoid quality loss
                    acodec = 'copy' if a.codec.lower() in self.settings.audio_codecs else self.settings.audio_codecs[0]
                    # Audio channel adjustments
                    if self.settings.max_audio_channels and a.audio_channels > self.settings.max_audio_channels:
                        audio_channels = self.settings.maxchannels
                        if acodec == 'copy':
                            acodec = self.settings.acodec[0]
                        abitrate = self.settings.max_audio_channels * self.settings.abitrate
                    else:
                        audio_channels = a.audio_channels
                        abitrate = a.audio_channels * self.settings.audio_bitrate

                    # Bitrate calculations/overrides
                    if self.settings.audio_bitrate == 0:
                        self.log.debug("Attempting to set bitrate based on source stream bitrate.")
                        try:
                            abitrate = a.bitrate / 1000
                        except:
                            self.log.warning(
                                "Unable to determine audio bitrate from source stream %s, defaulting to 256 per channel." % a.index)
                            abitrate = a.audio_channels * 256
                    afilter = self.settings.audio_filter

                self.log.debug("Audio codec: %s." % acodec)
                self.log.debug("Channels: %s." % audio_channels)
                self.log.debug("Bitrate: %s." % abitrate)
                self.log.debug("Language: %s" % a.metadata['language'])
                self.log.debug("Filter: %s" % afilter)


                # If the iOSFirst option is enabled, disable the iOS option after the first audio stream is processed
                if self.settings.ios_audio and self.settings.ios_first_track_only:
                    self.log.debug("Not creating any additional iOS audio streams.")
                    self.settings.ios_audio = False

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
                if self.settings.ios_move_last and iosdata:
                    iosdata['disposition'] = 'none'
                    audio_settings.update({l: iosdata})
                    l += 1

                if self.settings.audio_copy_original and acodec != 'copy':
                    self.log.info("Adding copy of original audio track in format %s" % a.codec)
                    audio_settings.update({l: {
                        'map': a.index,
                        'codec': 'copy',
                        'language': a.metadata['language'],
                        'disposition': 'none',
                    }})
                    l += 1

        return audio_settings

    def generatesubtitleoptions(self):
        self.log.info("Reading audio streams.")
        info = self.selectlanguage(self.mediainfo.subtitle)
        subtitle_settings = {}
        l = 0
        self.log.info("Reading subtitle streams.")

        for s in info:
            if s.codec.lower() not in self.__class__.badcodecs:
                if self.settings.embed_subs:
                    subtitle_settings.update({l: {
                        'map': s.index,
                        'codec': self.settings.subtitle_codecs[0],
                        'language': s.metadata['language'],
                        'encoding': self.settings.subtitle_encoding,
                        # 'forced': s.sub_forced,
                        # 'default': s.sub_default
                    }})
                    self.log.info("Creating subtitle stream %s from source stream %s." % (l, s.index))
                    l = l + 1


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

        if self.mediainfo.video.codec.lower() in ['x265', 'h265', 'hevc']:
            options.extend(['-tag:v', 'hvc1'])
            self.log.info("Tagging copied video stream as hvc1")

        return options


class MKV(GenericContainer):
    name = 'mkv'

    def generatevideooptions(self):
        pass

    def generateaudiooptions(self):
        pass
    def generatesubtitleoptions(self):
        pass


Containers = {}

for cls in GenericContainer.__subclasses__():
    Containers[cls.name] = cls
    
if __name__ == '__main__':
    import converter

    conv = converter.Converter('/usr/local/bin/ffmpeg', '/usr/local/bin/ffprobe')
    mkvinfo = conv.probe('/Users/Jon/Downloads/in/The.Polar.Express.(2004).1080p.BluRay.MULTI.x264-DiG8ALL.mkv')
    test = MP4('defaults', mkvinfo)
    print(Containers)

    print(test.videooptions)

    print(test.audiooptions)
