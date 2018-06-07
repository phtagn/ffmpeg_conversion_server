# coding=utf-8
import logging
from converter.streamformats import StreamFormatFactory
from typing import Dict
from streamtemplates import filterlanguages
from streamtemplates import VideoStreamTemplate, AudioStreamTemplate, SubtitleStreamTemplate
from info.streaminfo import VideoStreamInfo, AudioStreamInfo, SubtitleStreamInfo, TargetVideoStream, TargetAudioStream, \
    TargetSubtitleStream, Container, TargetContainer

log = logging.getLogger(__name__)


class OptionGenerator(object):
    supported_codecs = {'video': [],
                        'audio': [],
                        'subtitle': []}
    extension = ''  # type: str
    ffmpeg_format = ''  # type: str
    badcodecs = []  # type: list
    name = 'mp4'
    defaults = {
        'video': {
            'prefer_method': 'option(copy, transcode, override, default=copy)',
            'accepted_track_formats': 'force_list(default=list(h264, h265, hevc))',
            'transcode_to': 'string(default=h264)'
        },

        'audio': {
            'accepted_track_formats': 'force_list(default=list(aac, ac3))',
            'transcode_to': 'string(default=aac)',
            'force_create_tracks': 'force_list(default=None)',
            'audio_copy_original': 'boolean(default=False)',
            'create_multiple_stereo_tracks': 'boolean(default=False)',
        },

        'subtitle': {
            'accepted_track_formats': 'force_list(default=list(mov_text))',
        },

        'process_same': 'boolean(default=False)',
        'preopts': 'string(default=None)',
        'postopts': 'string(default=None)'
    }

    def __init__(self, cfg, target) -> None:

        self.config = cfg

        target = 'mp4'
        self.video = {'prefer_method': cfg['Containers'][target]['video'].get('prefer_method'),
                      'transcode_to': cfg['Containers'][target]['video'].get('transcode_to'),
                      'accepted_track_formats': cfg['Containers'][target]['video'].get('accepted_track_formats')}

        self.audio = {'transcode_to': cfg['Containers'][target]['audio'].get('transcode_to'),
                      'force_create_tracks': cfg['Containers'][target]['audio'].get('force_create_tracks'),
                      'create_multiple_stereo_tracks': cfg['Containers'][target]['audio'].get(
                          'create_multiple_stereo_tracks'),
                      'accepted_languages': cfg['Languages'].get('audio')
                      }

        self.subtitle = {'accepted_languages': cfg['Languages'].get('subtitle')}

        self.preopts = cfg['Containers'][target].get('preopts') if cfg['Containers'][target].get('preopts') else []

        self.postopts = cfg['Containers'][target].get('postopts') if cfg['Containers'][target].get('postopts') else []

        self._audioencoders = []
        self._videoencoders = []
        self._subtitleencoders = []

        self._videostreamtemplate = VideoStreamTemplate(self.config['TrackFormats'],
                                                        self.config['Containers'][target]['video'][
                                                            'accepted_track_formats'])

        self._audiostreamtemplate = AudioStreamTemplate(self.config['TrackFormats'],
                                                        self.config['Containers'][target]['audio'][
                                                            'accepted_track_formats'])

        self._subtitestreamtemplate = SubtitleStreamTemplate(self.config['TrackFormats'],
                                                             self.config['Containers'][target]['subtitle'][
                                                                 'accepted_track_formats']
                                                             )

    def create_streams(self, source, target) -> TargetContainer:
        targetcontainer = TargetContainer(target)

        for videostream in source.videostreams:

            index = len(targetcontainer.videostreams) + 1 if targetcontainer.videostreams else 0

            print(source.videostreams.index(videostream))

            if self.video['prefer_method'] == 'copy' and videostream.codec in self._videostreamtemplate.codecs:
                s = TargetVideoStream(index=index,
                                      pix_fmt=videostream.pix_fmt,
                                      bitrate=videostream.bitrate,
                                      codec=videostream.codec,
                                      width=videostream.width,
                                      height=videostream.height,
                                      level=videostream.level,
                                      profile=videostream.profile,
                                      sourceindex=videostream.index,
                                      willtranscode=False)

            elif self.video['prefer_method'] == 'override' and videostream.codec in self._videostreamtemplate.codecs:
                s = self._videostreamtemplate.getStreamInfo(videostream, index)

            else:
                fmt = self.config['TrackFormats'][self.video['transcode_to']]
                if fmt.get('pix_fmts'):
                    pix_fmt = fmt['pix_fmts'][0]
                else:
                    pix_fmt = None

                s = TargetVideoStream(index=index,
                                      codec=self.video['transcode_to'],
                                      bitrate=fmt.get('max_bitrate'),
                                      pix_fmt=pix_fmt,
                                      width=fmt.get('max_width'),
                                      height=fmt.get('max_height'),
                                      profile=fmt.get('profile'),
                                      level=fmt.get('level'),
                                      sourceindex=videostream.index,
                                      willtranscode=True)

            targetcontainer.videostreams = s

            for audiostream in source.audiostreams:
                index = len(targetcontainer.audiostreams) + 1 if targetcontainer.audiostreams else 0

                if audiostream.codec in self._audiostreamtemplate.codecs:
                    s = self._audiostreamtemplate.getStreamInfo(audiostream, index)

                    targetcontainer.audiostreams = s

                for acodec in self.audio['force_create_tracks']:
                    fmt = self.config['TrackFormats'][acodec]
                    s = TargetAudioStream(index=index,
                                          codec=acodec,
                                          channels=fmt.get('max_channels') if acodec != audiostream.codec else min(
                                              fmt.get('max_channels'), audiostream.channels),
                                          bitrate=fmt.get('max_bitrate') if acodec != audiostream.codec else min(
                                              fmt.get('max_bitrate'), audiostream.bitrate),
                                          language=audiostream.language,
                                          sourceindex=audiostream.index,
                                          willtranscode=True)

                    targetcontainer.audiostreams = s

            for k in targetcontainer.getaudiotranscode():
                if k in targetcontainer.audioNotTranscode():
                    targetcontainer.audiostreams.remove(k)

            for stream in source.subtitlestreams:
                index = len(targetcontainer.subtitlestreams) + 1 if targetcontainer.subtitlestreams else 0
                s = self._subtitestreamtemplate.getStreamInfo(stream, index)

                targetcontainer.subtitlestreams = s

            return targetcontainer

    def g(self, sourcecontainer, targetcontainer):
        encs = []

        for stream in sourcecontainer.videostreams:
            targetstreams = targetcontainer.getvideofromsource(stream.index)
            for tgtstream in targetstreams:
                if tgtstream == stream:
                    enc = StreamFormatFactory.get(stream.codec).getEncoder('copy')({'map': tgtstream.sourceindex,
                                                                                    'src_height': stream.height,
                                                                                    'src_width': stream.width})
                    encs.append(enc)
                else:
                    params = self.config['TrackFormats'][tgtstream.codec]
                    enc = StreamFormatFactory.get(tgtstream.codec).getEncoder(params.get('encoder', 'default'))(
                        {'map': tgtstream.sourceindex,
                         'bitrate': tgtstream.bitrate,
                         'profile': tgtstream.profile,
                         'pix_fmt': tgtstream.pix_fmt,
                         'level': tgtstream.level,
                         'height': tgtstream.height,
                         'width': tgtstream.width})

                    # TODO: add mode and filter.
                    if self.config['Encoders'].get(tgtstream.codec, None):
                        encoderopts = self.config['Encoders'][tgtstream.codec]
                        enc.add_options(encoderopts)

                    encs.append(enc)

        for stream in sourcecontainer.audiostreams:
            targetstreams = targetcontainer.getaudiofromsource(stream.index)
            for tgtstream in targetstreams:
                if tgtstream == stream:
                    enc = StreamFormatFactory.get(stream.codec).getEncoder('copy')({'map': tgtstream.sourceindex,
                                                                                    'language': tgtstream.language})
                    encs.append(enc)

                else:
                    params = self.config['TrackFormats'][tgtstream.codec]
                    enc = StreamFormatFactory.get(tgtstream.codec).getEncoder(params.get('encoder', 'default'))(
                        {'map': tgtstream.sourceindex,
                         'bitrate': tgtstream.bitrate,
                         'channels': tgtstream.channels,
                         'language': tgtstream.language})

                    if self.config['Encoders'].get(tgtstream.codec, None):
                        encoderopts = self.config['Encoders'][tgtstream.codec]
                        enc.add_options(encoderopts)

                    encs.append(enc)

        for stream in sourcecontainer.subtitlestreams:
            targetstreams = targetcontainer.getsubtitlefromsource(stream.index)
            for tgtstream in targetstreams:
                if tgtstream == stream:
                    enc = StreamFormatFactory.get(stream.codec).getEncoder('copy')({'map': tgtstream.sourceindex,
                                                                                    'language': tgtstream.language})
                    encs.append(enc)

                else:
                    params = self.config['TrackFormats'][tgtstream.codec]
                    enc = StreamFormatFactory.get(tgtstream.codec).getEncoder(params.get('encoder', 'default'))(
                        {'map': tgtstream.sourceindex,
                         'language': tgtstream.language})

                    if self.config['Encoders'].get(tgtstream.codec, None):
                        encoderopts = self.config['Encoders'][tgtstream.codec]
                        enc.add_options(encoderopts)

                    encs.append(enc)

        for enc in encs:
            print(enc.parse_options())
        return encs



class ContainerFactory(object):
    containers = {}

    @classmethod
    def register(cls, ctn):
        cls.containers.update({ctn.name: ctn})

    @staticmethod
    def get(ctn: str, cfg: Dict):
        if ctn in ContainerFactory.containers:
            return ContainerFactory.containers[ctn](cfg)


ContainerFactory.register(OptionGenerator)


class UnsupportedContainer(Exception):
    pass


if __name__ == '__main__':
    import configuration

    cfgmgr = configuration.cfgmgr()
    cfgmgr.load('defaults.ini')
    cfg = cfgmgr.cfg
    op = OptionGenerator(cfg, 'mp4')
    import converter.ffmpeg2

    ff = converter.ffmpeg2.FFMpeg('/usr/local/bin/ffmpeg', '/usr/local/bin/ffprobe')
    mediainfo = ff.probe('/Volumes/Downloads/Pentagon Papers.mkv')
    toto = op.create_streams(mediainfo, 'mp4')
    op.g(mediainfo, toto)
    print('yeah')
