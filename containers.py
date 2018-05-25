# coding=utf-8
import abc
from converter.encoders import EncoderFactory
from converter.ffmpeg import MediaInfo, MediaStreamInfo
import logging
import languagecode
import sys
import os
from typing import Union, Dict

log = logging.getLogger(__name__)


class GenericContainer(object):
    __metaclass__ = abc.ABCMeta

    supported_codecs = {'video': [],
                        'audio': [],
                        'subtitle': []}
    extension = ''  # type: str
    ffmpeg_format = ''  # type: str
    badcodecs = []  # type: list
    name = ''
    defaults = {
        'prefer_method': 'option(copy, transcode, override, default=copy)',
        'video_codecs': 'force_list(default=list(h264, h265, hevc))',
        'transcode_with': 'string(default=h264)',
        'audio_codecs': 'force_list(default=list(aac, ac3))',
        'audio_create_streams': 'force_list(default=None)',
        'audio_copy_original': 'boolean(default=False)',
        'subtitle_codecs': 'force_list(default=list(mov_text))',
        'process_same': 'boolean(default=False)',
        'embed_subs': 'boolean(default=True)',
        'preopts': 'string(default=None)',
        'postopts': 'string(default=None)',
        'pix_fmts': 'force_list(default=None)',
        'profiles': 'force_list(default=None)'
    }

    def __init__(self, cfg) -> None:

        self.streams = {'video': [], 'audio': [], 'subtitle': []}

        self.audiolanguages = cfg['Languages']['audio']
        self.subtitlelanguages = cfg['Languages']['subtitle']
        self.codecopts = cfg['Codecs']

        for opt in self.options:
            setattr(self, opt, self.options.get(opt))

        self.preopts = list(self.preopts) if self.preopts else []
        self.postopts = list(self.postopts) if self.preopts else []

        if cfg['FFMPEG']['threads']:
            self.postopts.extend(['-threads', cfg['FFMPEG']['threads']])

        self.format_options = ['-f', self.__class__.ffmpeg_format]

        for codec in self.video_codecs:
            if not self.supports(codec, 'video'):
                self.video_codecs.remove(codec)
                log.info('Codec %s, not supported by container %s, removing. Supported Codecs are {%s}',
                         codec,
                         self.__class__.name,
                         self.__class__.supported_codecs['video'])

        for codec in self.audio_codecs:
            if not self.supports(codec, 'audio'):
                self.video_codecs.remove(codec)
                log.info('Codec %s, not supported by container %s, removing. Supported Codecs are {%s}',
                         codec,
                         self.__class__.name,
                         self.__class__.supported_codecs['audio'])

        for codec in self.subtitle_codecs:
            if not self.supports(codec, 'subtitle'):
                self.subtitle_codecs.remove(codec)
                log.info('Codec %s, not supported by container %s, removing. Supported Codecs are {%s}',
                         codec,
                         self.__class__.name,
                         self.__class__.supported_codecs['subtitle'])

        if getattr(self, 'transcode_with', None) and self.transcode_with not in self.video_codecs:
            self.video_codecs.append(self.transcode_with)

    def parse_options(self):
        allopts = []

        for typ in self.streams:
            for stream in self.streams[typ]:
                for streamnumber in stream:
                    allopts.extend(stream[streamnumber].parse_options(stream=streamnumber))
        allopts.extend(self.format_options)
        return allopts

    @abc.abstractmethod
    def _container_processvideo(self, info, stream=0):
        pass

    @abc.abstractmethod
    def _container_processsaudio(self, info, stream=0):
        pass

    @abc.abstractmethod
    def _container_processsubtitle(self, info, stream=0):
        pass

    @classmethod
    def supports(cls, codec, codec_type):
        if codec in cls.supported_codecs[codec_type] or cls.supported_codecs[codec_type][0] == '*':
            return True
        return False

    def processstreams(self, mediainfo):
        if mediainfo.video:
            self._processvideo(mediainfo)

        if mediainfo.audio:
            self._processaudio(mediainfo.audio)

        if mediainfo.subtitle:
            self._processsubtitle(mediainfo.subtitle)

    def _processvideo(self, mediainfo, stream=0):
        log.info('Processing video stream')

        codecopts = self.codecopts
        vcodec = None
        info = mediainfo.video

        if self.prefer_method == 'copy' and info.codec in self.video_codecs:
            vcodec = EncoderFactory.get('copy', 'video', codecopts)

        elif self.prefer_method == 'transcode' or info.codec not in self.video_codecs:
            vcodec = EncoderFactory.get(self.transcode_with, 'video', codecopts)
            vcodec.add_options({'src_width': getattr(info, 'video_width', None),
                                'src_height': getattr(info, 'video_height', None)})

        elif self.prefer_method == 'override':
            override = False
            vcodec = EncoderFactory.get(self.transcode_with, 'video', codecopts)
            opts = vcodec.safeopts

            if info.codec != self.transcode_with:
                override = True

            if info.pix_fmt.lower() not in self.pix_fmts and opts.get('pix_fmt'):
                override = True

            if opts.get('bitrate'):
                vbr = self.estimatevideobitrate(mediainfo)
                if vbr > opts.get('bitrate'):
                    override = True

            if opts.get('width') and opts.get('width') > info.video_width:
                override = True
                vcodec.add_options({'src_width': getattr(info, 'video_width', None),
                                    'src_height': getattr(info, 'video_height', None)})

            if opts.get('profile') and hasattr(info, 'profile') and info.profile not in self.profiles:
                override = True

            if opts.get('level') and hasattr(info, 'video_level') and info.video_level / 10 > opts.get['level']:
                override = True

            if opts.get('filter'):
                override = True

            if override == False:
                vcodec = EncoderFactory.get('copy', 'video', codecopts)

        if vcodec.codec_name in ['h265', 'hevc'] or (info.codec in ['h265', 'hevc'] and vcodec.codec_name == 'copy'):
            self.postopts.extend(['-tag:v', 'hvc1'])

        if vcodec:
            vcodec.add_options({'map': info.index})
            self.streams['video'] = [{stream: vcodec}]
        else:
            log.debug('Could not define video codec')

    def _processaudio(self, info, stream=0):
        codecopts = self.codecopts
        acodecs = []
        info = self.selectlanguage(info, relax=True)
        audio_stream_number = stream
        for s in info:

            if s.codec in self.audio_codecs:
                acodec = EncoderFactory.get('copy', 'audio', codecopts)
                acodec.add_options({'map': s.index,
                                    'language': s.metadata['language']
                                    })
                #                if self.aac_adtstoasc:
                #                    acodec.add_options({'bsf': True})
                acodecs.append({audio_stream_number: acodec})
                audio_stream_number += 1

            # We want to create extra audio channels with the proper specs if we have not copied them before
            if s.codec not in self.__class__.badcodecs and self.audio_create_streams:
                for c in self.audio_create_streams:
                    acodec = EncoderFactory.get(c, 'audio', codecopts)
                    if (s.audio_channels > acodec.safeopts.get('channels', s.audio_channels)
                            or (s.bitrate and s.bitrate > acodec.safeopts.get('bitrate', s.bitrate))
                            or acodec.safeopts.get('filter')
                            or s.codec != acodec.codec_name):

                        acodec.add_options({'map': s.index,
                                            'language': s.metadata['language']})
                        acodecs.append({audio_stream_number: acodec})
                        audio_stream_number += 1

            r, audio_stream_number = self._container_processsaudio(s, audio_stream_number)

            if r:
                acodecs.extend(r)

        if acodecs:
            self.streams['audio'] = acodecs

    def _processsubtitle(self, info, subfile=None, stream=0):
        codecopts = self.codecopts
        scodecs = []
        scodec = None
        info = self.selectlanguage(info, relax=False)
        sub_stream_number = stream

        for s in info:
            if s.codec in self.subtitle_codecs:
                scodec = EncoderFactory.get('copy', 'subtitle', codecopts)
            elif s.codec not in self.__class__.badcodecs:
                scodec = EncoderFactory.get(self.subtitle_codecs[0], 'subtitle', codecopts)

            if scodec:
                self.streams['subtitle'] = {sub_stream_number: scodecs}
                scodecs.append({sub_stream_number: scodec})
                sub_stream_number += 1

        if scodecs:
            self.streams['subtitle'] = scodecs
            self.preopts.extend(['-fix_sub_duration'])

    @staticmethod
    def estimatevideobitrate(info):
        try:
            total_bitrate = info.format.bitrate
            audio_bitrate = 0
            for a in info.audio:
                if a.bitrate:
                    audio_bitrate += a.bitrate
            log.debug("Total bitrate is %s." % info.format.bitrate)
            log.debug("Total audio bitrate is %s." % audio_bitrate)
            log.debug("Estimated video bitrate is %s." % (total_bitrate - audio_bitrate))
            return ((total_bitrate - audio_bitrate) / 1000) * .95
        except:
            return info.format.bitrate / 1000

    def selectlanguage(self, streams, relax=False):
        valid_language_streams = []
        oklanguages = list(map(languagecode.validate, self.audiolanguages))
        for s in streams:
            if 'language' in s.metadata:
                s.metadata['language'] = languagecode.validate(s.metadata['language'])
            else:
                s.metadata['language'] = 'und'

            if s.metadata['language'] in oklanguages:
                valid_language_streams.append(s)

        if not valid_language_streams and relax is True:
            log.info('No valid language streams, selecting all language streams')
            return streams
        else:
            return valid_language_streams

    @property
    def postprocess(self):
        return []


class MP4(GenericContainer):
    name = 'mp4'
    extension = '.mp4'
    ffmpeg_format = 'mp4'

    supported_codecs = {
        'video': ['copy', 'h264', 'h265', 'nvenc_h264', 'nvenc_h265', 'h264vaapi', 'h264_qsv', 'hevc_qsv', 'x264', 'hevc'],
        'audio': ['copy', 'aac', 'libfdk_aac', 'ac3'],
        'subtitle': ['copy', 'mov_text']}

    badcodecs = ['truehd', 'pgssub', 'dvdsub', 's_hdmv/pgs', 'hdmv_pgs_subtitle', 'dvd_subtitle', 'pgssub',
                 'dvb_teletext', 'dvb_subtitle']

    defaults = GenericContainer.defaults.copy()

    defaults.update({
        'relocate_moov': 'boolean(default=False)',
        'ios_audio': 'boolean(default=False)',
        'ios_default_language_only': 'boolean(default=False)',
        'ios_audio_filter': 'string(default=None)'
    })

    def __init__(self, cfg):
        """Handles initial loading of settings from settings manager as well as settings validation
        comparing them to both what's allowed in the container and the codec supported by the program"""
        self.options = cfg['Containers']['mp4']
        super(self.__class__, self).__init__(cfg)

    def _container_processvideo(self, info):
        return None

    def _container_processsaudio(self, s, stream=0):
        audio_stream_number = stream
        acodecs = []
        if s.codec not in self.__class__.badcodecs:
            if self.ios_audio and s.audio_channels <= 2 and s.codec == 'aac' and s.codec not in self.audio_codecs:
                acodec = EncoderFactory.get('copy', 'audio', self.codecopts)
                acodec.add_options({'map': s.index,
                                    'language': s.metadata['language']})
                acodecs.append({audio_stream_number: acodec})
                audio_stream_number += 1

            elif self.ios_audio and s.audio_channels > 2:
                acodec = EncoderFactory.get('aac', 'audio', {
                    'bitrate': 256,
                    'channels': 2,
                    'filter': getattr(self, 'ios_audio_filter', None),
                    'map': s.index,
                    'language': s.metadata['language']
                })
                acodecs.append({audio_stream_number: acodec})
                audio_stream_number += 1

        return acodecs, audio_stream_number

    def _container_processsubtitle(self, info):
        return None

    @property
    def postprocess(self):
        _postprocess = []

        # if GenericContainer.postprocess:
        #    _postprocess.extend(GenericContainer.postprocess)

        def QTFS(inputfile, *args, **kwargs):
            try:
                from qtfaststart import processor, exceptions
            except:
                log.error('Please install qtfaststart: pip install qtfaststart')

            try:
                qtfsfile = inputfile.decode(sys.getfilesystemencoding()) + '.qtfs'
            except:
                qtfsfile = inputfile + '.qtfs'

            if os.path.exists(qtfsfile):
                os.remove(qtfsfile)

            try:
                processor.process(inputfile, qtfsfile)
            except:
                log.exception('QTFS failed')

            try:
                os.remove(inputfile)
                os.rename(qtfsfile, inputfile)
            except:
                log.error('Error cleaning up QTFS temp files')

        if self.relocate_moov:
            _postprocess.append(QTFS)
        return _postprocess


class MKV(GenericContainer):
    extension = '.mkv'
    supported_codecs = {'video': ['*'],
                        'audio': ['*'],
                        'subtitle': ['*']}
    badcodecs = ['truehd']
    ffmpeg_format = 'matroska'
    name = 'mkv'

    def __init__(self, cfg):
        """Handles initial loading of settings from settings manager as well as settings validation
        comparing them to both what's allowed in the container and the codec supported by the program"""
        self.options = cfg['Containers']['mkv']
        super(self.__class__, self).__init__(cfg)


    def _container_processvideo(self, info, stream=0):
        return []


    def _container_processsaudio(self, info, stream=0):
        return [], stream


    def _container_processsubtitle(self, info, stream=0):
        return [], stream


class ContainerFactory(object):

    containers = {}
    @classmethod
    def register(cls, ctn):
        cls.containers.update({ctn.name: ctn})

    @staticmethod
    def get(ctn: str, cfg: Dict) -> Union[MP4, MKV]:
        if ctn in ContainerFactory.containers:
            return ContainerFactory.containers[ctn](cfg)

ContainerFactory.register(MKV)
ContainerFactory.register(MP4)



class UnsupportedContainer(Exception):
    pass