"""
Module to generate options based on a target container.
"""
from converter.target import TargetContainerFactory
from converter.streamformats import StreamFormatFactory


class OptionGenerator(object):

    def __init__(self, cfg) -> None:
        self.config = cfg

    def get_options(self, targetcontainer):
        encs = {}
        l = 0
        for tgtstream in targetcontainer.videostreams:

            encoder_name = self.config['TrackFormats'][tgtstream.codec].get('encoder', 'default')
            if tgtstream.willtranscode:
                enc = StreamFormatFactory.get_format(tgtstream.codec).getEncoder(encoder_name)(
                    {'map': tgtstream.sourceindex,
                     'bitrate': tgtstream.bitrate,
                     'profile': tgtstream.profile,
                     'pix_fmt': tgtstream.pix_fmt,
                     'level': tgtstream.level,
                     'height': tgtstream.height,
                     'width': tgtstream.width,
                     'src_height': tgtstream.src_height,
                     'src_width': tgtstream.src_width})

            else:
                enc = StreamFormatFactory.get_format(tgtstream.codec).getEncoder('copy')(
                    {'map': tgtstream.sourcestream.index,
                     'src_height': tgtstream.sourcestream.height,
                     'src_width': tgtstream.sourcestream.width,
                     'disposition': tgtstream.sourcestream.disposition})

            encoderoptions = self.config['Encoders'].get(encoder_name)
            if encoderoptions:
                enc.add_options(encoderoptions)
            encs.update({l: enc})
            l += 1

        for tgtstream in targetcontainer.audiostreams:
            if tgtstream.willtranscode:
                enc = StreamFormatFactory.get_format(tgtstream.codec).getEncoder(
                    self.config['Encoders'].get('encoder', 'default'))(
                    {'bitrate': tgtstream.bitrate,
                     'channels': tgtstream.channels,
                     'language': tgtstream.language,
                     'map': tgtstream.sourcestream.index})
            else:
                enc = StreamFormatFactory.get_format(tgtstream.codec).getEncoder('copy')(
                    {'language': tgtstream.language,
                     'map': tgtstream.sourcestream.index,
                     'disposition': tgtstream.sourcestream.disposition})

            encoderoptions = self.config['Encoders'].get(encoder_name)
            if encoderoptions:
                enc.add_options(encoderoptions)
            encs.update({l: enc})
            l += 1

        for tgtstream in targetcontainer.subtitlestreams:
            if tgtstream.willtranscode:
                enc = StreamFormatFactory.get_format(tgtstream.codec).getEncoder(
                    self.config['Encoders'].get('encoder', 'default'))(
                    {'language': tgtstream.language,
                     'map': tgtstream.sourcestream.index})
            else:
                enc = StreamFormatFactory.get_format(tgtstream.codec).getEncoder('copy')(
                    {'language': tgtstream.language,
                     'map': tgtstream.sourcestream.index})

            encoderoptions = self.config['Encoders'].get(encoder_name)
            if encoderoptions:
                enc.add_options(encoderoptions)

            encs.update({l: enc})
            l += 1

        format_options = targetcontainer.format.parse_options()
        track_options = []
        for e in encs:
            track_options.extend(encs[e].parse_options(e))

        return track_options + format_options


if __name__ == '__main__':
    import configuration
    import converter.ffmpeg

    cfgmgr = configuration.cfgmgr()
    cfgmgr.load('defaults.ini')
    cfg = cfgmgr.cfg
    Tg = TargetContainerFactory(cfg, 'mp4')

    ff = converter.ffmpeg.FFMpeg('/usr/local/bin/ffmpeg', '/usr/local/bin/ffprobe')
    SourceContainer = ff.probe('/Users/jon/Downloads/Geostorm 2017 1080p FR EN X264 AC3-mHDgz.mkv')
    TargetContainer = Tg.build_target_container(sourcecontainer=SourceContainer)
    og = OptionGenerator(cfg)
    fo = og.get_options(TargetContainer)
    print(' '.join(fo))
    print('yeah')
