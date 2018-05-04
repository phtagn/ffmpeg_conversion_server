# coding=utf-8
import logging
import os
import sys
from logging.config import fileConfig
from typing import List

import languagecode
from converter.avcodecs import *
from converter.ffmpeg import MediaInfo


class FFMPEGAdapter(object):

    def __init__(self, settings, mediainfo: MediaInfo, logger: logging.Logger = None):
        if logger:
            self.log = logger
        else:
            fileConfig(os.path.join(os.path.dirname(sys.argv[0]), 'logging.ini'),
                       defaults={'logfilename': os.path.join(os.path.dirname(sys.argv[0]), 'server.log')})
            self.log = logging.getLogger(__name__)

        self.settings = settings.SettingsManager.getsettings('defaults')
        self.mediainfo = mediainfo

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
                        self.settings.audio_languages[
                            0] == 'und' and self.settings.audio_default_language == 'und'):
                    output.append(s)

        if not output:
            for s in streams:
                output.append(s)

        return output

    def estimateVideoBitrate(self) -> float:
        total_bitrate = self.mediainfo.format.bitrate
        audio_bitrate = 0

        for a in self.mediainfo.audio:
            audio_bitrate += a.bitrate

        self.log.debug("Total bitrate is %s." % self.mediainfo.format.bitrate)
        self.log.debug("Total audio bitrate is %s." % audio_bitrate)
        self.log.debug("Estimated video bitrate is %s." % (total_bitrate - audio_bitrate))
        return ((total_bitrate - audio_bitrate) / 1000) * .95

    def selecttrack(self) -> List[MediaInfo]:
        """
        Returns a list tracks based on what is compatible with the container
        """
        pass

    def generateVoptions(self, stream) -> Dict[str, BaseCodec]:
        self.log.info("Reading video stream.")
        self.log.info("Video codec detected: %s." % self.mediainfo.video.codec)
        preferredcodec = self.settings[self.container.name]
        videosettings = self.settings['Codecs']['Video']

        info = self.mediainfo.video
        vbr = self.estimateVideoBitrate()
        vcodec = None
        print(video_codec_dict)

        self.log.info(f"Pix Fmt: {info.pix_fmt}.")
        if self.settings.pix_fmts and info.pix_fmt.lower() not in self.settings.pix_fmts:
            vcodec = video_codec_dict[self.settings.video_codecs[0]]() if not vcodec else vcodec
            opt = {'pix_fmt': self.settings.pix_fmts[0]}
            vcodec.add_options(opt)
            if self.settings.video_profiles:
                vcodec.add_options({'profile': self.settings.video_profiles[0]})

        self.log.info(f"File video bitrate: {info.bitrate} -> {self.settings.video_bitrate} (vbr = {vbr})")
        if self.settings.video_bitrate and vbr > self.settings.video_bitrate:
            vcodec = video_codec_dict[self.settings.video_codecs[0]]() if not vcodec else vcodec
            vcodec.add_options({'bitrate': self.settings.video_bitrate})

        if self.settings.video_max_width and self.settings.video_max_width < info.video.width:
            vcodec = video_codec_dict[self.settings.video_codecs[0]]() if not vcodec else vcodec
            vcodec.add_options({'width': self.settings.video_max_width})

        if not vcodec and info.codec.lower() in self.settings.video_codecs:
            vcodec = video_codec_dict['copy']()

        if not vcodec:
            raise Exception('No codec could be selected')
        else:
            vcodec.add_options({'map': info.index})

        options = {'codec': vcodec}

        return options

        # TODO: deal with level

    def generateAoptions(self):
        """Generates a dictionary with audio options"""
        # Audio streams
        self.log.info("Reading audio streams.")
        info = self.selectlanguage(self.mediainfo.audio)

        audio_settings = {}  # type: dict
        l = 0
        for a in info:
            self.log.debug(f'Considering track {a.index}')
            # TODO : Weed out the codecs that we cannot convert from
            # if a.codec.lower() in self.__class__.badcodecs:
            #    self.log.info(
            #        f"MP4 containers do not support {a.codec.lower}, and converting does not work. Skipping stream {a.index}")
            #    continue

            self.log.info("Audio detected for stream #%s: %s [%s]." % (a.index, a.codec, a.metadata['language']))

            iosdata = None
            acodec = None
            # Create iOS friendly audio stream if the default audio stream has too many channels
            # (iOS only likes AAC stereo)
            if self.settings.ios_audio:
                self.log.info(f"Creating audio stream %s from source audio stream {a.index}.")

                if a.audio_channels > 2:

                    iOSbitrate: int = 256 if (self.settings.audio_bitrate * 2) > 256 else (
                                self.settings.audio_bitrate * 2)

                    acodec = audio_codec_dict['aac']() if not acodec else acodec
                    acodec.add_options({'channels': 2, 'bitrate': iOSbitrate})
                    if self.settings.ios_audio_filter:
                        acodec.add_options({'filter': self.settings.ios_audio_filter})

                    # Set disposition of first track to avoid iOS playing several audio tracks at once
                    if l == 0:
                        acodec.add_options({'disposition': 'default'})
                        self.log.info("Audio track is number %s setting disposition to %s" % (str(l), 'default'))
                    else:
                        acodec.add_options({'disposition': 'none'})
                        self.log.info("Audio track is number %s setting disposition to %s" % (str(l), 'none'))

                    # if self.settings.ios_audio_filter:
                    acodec.add_options({'filter': self.settings.ios_audio_filter})

                    acodec.add_options({'language': a.metadata['language']})
                    acodec.add_options({'map': a.index})
                    iosdata = {'codec': acodec}

                    self.log.debug(f"Audio codec: aac")
                    self.log.debug(f"Channels: {acodec.safeopts['channels']}")
                    # self.log.debug(f"Filter: {acodec.safeopts['filter']}")
                    # self.log.debug(f"Bitrate: {acodec.safeopts['bitrate']}")
                    self.log.debug(f"Language: {acodec.safeopts['language']}")
                    self.log.debug(f"Disposition: {acodec.safeopts['disposition']}")
                    self.log.debug(f"Map: {acodec.safeopts['map']}")

                    if not self.settings.ios_move_last:
                        audio_settings.update({l: iosdata})
                        l += 1

                    acodec = None
                # If the iOS audio option is enabled and the source audio channel is only stereo,
                # the additional iOS channel will be skipped and a single AAC 2.0 channel
                # will be made regardless of codec preference to avoid multiple stereo channels
                self.log.info("Creating audio stream %s from source stream %s." % (str(l), a.index))

                if a.audio_channels <= 2:
                    self.log.debug(
                        "Overriding default channel settings because iOS audio is enabled but the source is stereo [iOS-audio].")
                    acodec = audio_codec_dict['copy']() if a.codec == 'aac' else audio_codec_dict['aac']()
                    acodec.add_options({'channels': a.audio_channels})
                    acodec.add_options({'filter': self.settings.ios_audio_filter})

                    abitrate = a.audio_channels * 128 if (a.audio_channels * self.settings.audio_bitrate) > (
                            a.audio_channels * 128) else (a.audio_channels * self.settings.audio_bitrate)
                    acodec.add_options({'bitrate': abitrate})

            # If desired codec is the same as the source codec, copy to avoid quality loss

            # Audio channel adjustments
            if self.settings.max_audio_channels and a.audio_channels > self.settings.max_audio_channels:
                acodec = audio_codec_dict[self.settings.audio_codecs[0]]()
                acodec.add_options({'channels': self.settings.max_audio_channels})
                acodec.add_options({'bitrate': self.settings.max_audio_channels * self.settings.abitrate})

            # Bitrate calculations/overrides
            if self.settings.audio_bitrate == 0:
                self.log.debug("Attempting to set bitrate based on source stream bitrate.")
                try:
                    abitrate = a.bitrate / 1000
                except:
                    self.log.warning(
                        "Unable to determine audio bitrate from source stream %s, defaulting to 256 per channel." % a.index)
                    abitrate = a.audio_channels * 256

            abitrate = a.audio_channels * 256
            afilter = self.settings.audio_filter

            if not acodec and a.codec.lower() in self.settings.audio_codecs:
                acodec = audio_codec_dict['copy']()
                acodec.add_options({'language': a.metadata['language']})
                acodec.add_options({'map': a.index})
                acodec.add_options({'channels': a.audio_channels, 'bitrate': abitrate})

            afilter = self.settings.audio_filter

            # self.log.debug("Audio codec: %s." % acodec)
            # self.log.debug("Channels: %s." % audio_channels)
            # self.log.debug("Bitrate: %s." % abitrate)
            # self.log.debug("Language: %s" % a.metadata['language'])
            # self.log.debug("Filter: %s" % afilter)

            # If the iOSFirst option is enabled, disable the iOS option after the first audio stream is processed
            # if self.settings.ios_audio and self.settings.ios_first_track_only:
            #    self.log.debug("Not creating any additional iOS audio streams.")
            #    self.settings.ios_audio = False

            # Set first track as default disposition
            # if l == 0:
            #    disposition = 'default'
            #    self.log.info("Audio Track is number %s setting disposition to %s" % (a.index, disposition))
            # else:
            #    disposition = 'none'
            #    self.log.info("Audio Track is number %s setting disposition to %s" % (a.index, disposition))
            if acodec:
                audio_settings.update({l: {'codec': acodec}})
                l += 1
            # audio_settings.update(l: {
            #    'map': a.index,
            #    'codec': acodec,
            #    'channels': audio_channels,
            #    'bitrate': abitrate,
            #    'filter': afilter,
            #    'language': a.metadata['language'],
            #    'disposition': disposition,
            # }})

            # if acodec == 'copy' and a.codec == 'aac' and self.settings.aac_adtstoasc:
            #    audio_settings[l]['bsf'] = 'aac_adtstoasc'

            # l += 1

            # Add the iOS track last instead
            # if self.settings.ios_move_last and iosdata:
            #    iosdata['disposition'] = 'none'
            #    audio_settings.update({l: iosdata})
            #    l += 1

            # if self.settings.audio_copy_original and acodec != 'copy':
            #    self.log.info("Adding copy of original audio track in format %s" % a.codec)
            #    audio_settings.update({l: {
            #        'map': a.index,
            #        'codec': 'copy',
            #        'language': a.metadata['language'],
            #        'disposition': 'none',
            #    }})
            #    l += 1

        return audio_settings

    def generatesubtitleoptions(self) -> Dict[str, Union[str, int]]:
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

    def embedexternalsubtitles(self, subtitles: List[str]) -> Dict[str, Union[str, int]]:
        pass

    def generatepreopts(self) -> Dict[str, Union[str, int]]:
        """

        :return:
        :rtype:
        """
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








if __name__ == '__main__':
    import converter

    conv = converter.Converter('/usr/local/bin/ffmpeg', '/usr/local/bin/ffprobe')
    mkvinfo = conv.probe('/Users/Jon/Downloads/in/mini.mkv')
    test = FFMPEGAdapter('defaults', mkvinfo)
    video = test.generateVoptions()
    # print(toto['codec'].jopts)
    cmds = ['/usr/local/bin/ffmpeg',
            '-i',
            '/Users/Jon/Downloads/in/mini.mkv']

    result = video['codec'].parse_options(video['codec'].safeopts)
    cmds.extend(result)
    print(result)
    audio = test.generateAoptions()
    for k in audio:
        res = audio[k]['codec'].parse_options(audio[k]['codec'].safeopts, k)
        print(res)
        cmds.extend(res)
    print('-' * 10)
    cmds.extend(['-y', 'mini.mp4'])
    print(' '.join(cmds))
#    from subprocess import Popen, PIPE
#    import os
#    p = Popen(cmds, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE,
#                    close_fds=(os.name != 'nt'), startupinfo=None)
#    p.communicate()
#    while True:
#        ret = p.stderr.read(10)
#        if not ret:
#            break
