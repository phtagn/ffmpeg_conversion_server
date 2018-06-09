class TemplateFactory(object):
    """Returns a template object instantiated with the options from the config file"""
    @staticmethod
    def get_template(cfg, typ, trackformat):

        if trackformat in cfg['TrackFormats']:
            fmt = cfg['TrackFormats'][trackformat]
            if typ == 'video':
                return VideoStreamTemplate(codec=trackformat,
                                           pix_fmts=fmt.get('pix_fmts'),
                                           max_bitrate=fmt.get('max_bitrate'),
                                           max_height=fmt.get('max_height'),
                                           max_width=fmt.get('max_width'),
                                           profiles=fmt.get('profiles'),
                                           max_level=fmt.get('max_level'))
            elif typ == 'audio':
                return AudioStreamTemplate(codec=trackformat,
                                           max_channels=fmt.get('max_channels'),
                                           max_bitrate=fmt.get('max_bitrate'))

            elif typ == 'subtitle':
                return SubtitleStreamTemplate(codec=trackformat)
        else:
            raise Exception('No such format')


class VideoStreamTemplate(object):
    def __init__(self,
                 codec: str,
                 pix_fmts: list,
                 max_bitrate: int,
                 max_height: int,
                 max_width: int,
                 profiles: list,
                 max_level: int):

        self.codec = codec
        self.pix_fmts = pix_fmts
        self.max_bitrate = max_bitrate
        self.max_height = max_height
        self.max_width = max_width
        self.profiles = profiles
        self.max_level = max_level


class AudioStreamTemplate(object):
    def __init__(self, codec: str, max_channels: int, max_bitrate: int):
        self.codec = codec
        self.max_channels = max_channels
        self.max_bitrate = max_bitrate


class SubtitleStreamTemplate(object):
    def __init__(self, codec: str):
        self.codec = codec