# coding=utf-8
from collections import OrderedDict
from configobj import ConfigObj
from converter.encoders import Encoders, _VideoCodec, _AudioCodec, _SubtitleCodec
from converter.streamformats import *
from converter.streamoptions import EncoderOption

exposed_options = {
    Bitrate.__name__: 'integer(default=-1)',
    PixFmt.__name__: 'force_list(default=list(None))',
    Channels.__name__: 'integer(default=-1)',
    Level.__name__: 'float(default=-1)',
    Profile.__name__: 'force_list(default=list(High))',
    Height.__name__: 'integer(default=-1)',
    Bsf.__name__: 'string(default=None)',
    Crf.__name__: 'integer(default=-1)',
    Width.__name__: 'integer(default=-1)',
    Tag.__name__: 'string(default=None)'}

encoders = OrderedDict()

videocodecs = OrderedDict()
audiocodecs = OrderedDict()
subtitlecodecs = OrderedDict()

p = {}
preferred_encoders = OrderedDict()
for codec in Encoders._supported_codecs:
    optdict = OrderedDict()
    for opt in codec.supported_options:
        if opt.__name__ in exposed_options and issubclass(opt, EncoderOption):
            optdict.update({opt.__name__: exposed_options[opt.__name__]})
    if optdict:
        if issubclass(codec, _VideoCodec):
            videocodecs.update({codec.codec_name: optdict})
        elif issubclass(codec, _AudioCodec):
            audiocodecs.update({codec.codec_name: optdict})
        elif issubclass(codec, _SubtitleCodec):
            subtitlecodecs.update({codec.codec_name: optdict})

    if codec.produces in p and codec.codec_name != 'copy':
        p[codec.produces].append(codec.ffmpeg_codec_name)
    elif codec.codec_name != 'copy':
        p.update({codec.produces: [codec.ffmpeg_codec_name]})

for fmt in p:
    if len(p[fmt]) > 1:
        preferred_encoders[fmt] = f'string(default={p[fmt][0]})'

encoders = {**videocodecs, **audiocodecs, **subtitlecodecs}

videostreams = OrderedDict()
audiostreams = OrderedDict()
subtitlestreams = OrderedDict()

for fmt_name, fmt in StreamFormatFactory.formats.items():
    optdict = OrderedDict()
    for opt in fmt.supported_options:
        if opt.__name__ in exposed_options and issubclass(opt, IStreamOption):
            optdict.update({opt.__name__: exposed_options[opt.__name__]})
            if optdict:
                if issubclass(fmt, VideoStream):
                    videostreams.update({fmt.__name__[:-6].lower(): optdict})
                elif issubclass(fmt, AudioStream):
                    audiostreams.update({fmt.__name__[:-6].lower(): optdict})
                elif issubclass(fmt, SubtitleStream):
                    subtitlestreams.update({fmt.__name__[:-6].lower(): optdict})

streams = {**videostreams, **audiostreams, **subtitlestreams}

refreshers = {
    'plex': {'host': 'string(default=localhost)',
             'ssl': 'boolean(default=False)',
             'webroot': 'string(default=None)',
             'refresh': 'boolean(default=False)',
             'port': 'integer(default=32400)',
             'token': 'string(default=None)'},

    'sickrage': {'host': 'string(default=localhost)',
                 'ssl': 'boolean(default=False)',
                 'webroot': 'string(default=None)',
                 'refresh': 'boolean(default=False)',
                 'port': 'integer(default=32400)',
                 'api_key': 'string(default=None)'}
}

defaultconfig = {
    'FFMPEG': {
        'ffmpeg': 'string(default=/usr/local/bin/ffmpeg)',
        'ffprobe': 'string(default=/usr/local/bin/ffprobe)',
        'threads': 'string(default=auto)',
    },

    'Languages': {
        'audio': 'force_list(default=list(eng))',
        'subtitle': 'force_list(default=list(eng))',
        'tagging': 'string(default=eng)'
    },

    'Tagging': {
        'tagfile': 'boolean(default=True)',
        'preferred_show_tagger': 'string(default=tmdb)',
        'preferred_movie_tagger': 'string(default=tmdb)',
        'download_artwork': 'boolean(default=False)'
    },

    'File': {
        'work_directory': 'string(default=None)',
        'copy_to': 'string(default=None)',
        'move_to': 'string(default=None)',
        'delete_original': 'boolean(default=False)',
        'permissions': 'integer(default=777)'
    },
    'Containers': {
        'mp4': {
            'video': {
                'accepted_track_formats': 'force_list(default=list(h264, h265, hevc))',
                'default_format': 'string(default=hevc)',
                'prefer_copy': 'boolean(default=True)'
            },

            'audio': {
                'accepted_track_formats': 'force_list(default=list(aac, ac3))',
                'default_format': 'string(default=aac)',
                'force_create_tracks': 'force_list(default=None)',
                'prefer_copy': 'boolean(default=True)'
            },

            'subtitle': {
                'accepted_track_formats': 'force_list(default=list(mov_text))',
                'default_format': 'string(default=mov_text)',
                'prefer_copy': 'boolean(default=True)'
            },

            'post_processors': 'force_list(default=None)',
            'preopts': 'string(default=None)',
            'postopts': 'string(default=None)'
        }},
    'StreamFormats': streams,
    'PreferredEncoders': preferred_encoders,
    'EncoderOptions': encoders,
    'Refreshers': refreshers}

configspec = ConfigObj(defaultconfig, list_values=False)
