# coding=utf-8
from containers import ContainerFactory
from converter.avcodecs import CodecFactory
from configobj import ConfigObj


containersettings = {ctn.name: ctn.defaults for ctn in ContainerFactory.containers.values()}

codecsettings = {'video': {cdc.codec_name: cdc.defaults for cdc in CodecFactory.codecs['video'].values()},
                 'audio': {cdc.codec_name: cdc.defaults for cdc in CodecFactory.codecs['audio'].values()},
                 'subtitle': {cdc.codec_name: cdc.defaults for cdc in CodecFactory.codecs['subtitle'].values()}
                 }


defaultconfig = {
    'FFMPEG': {
        'ffmpeg': 'string(default=/usr/local/bin/ffmpeg)',
        'ffprobe': 'string(default=/usr/local/bin/ffprobe)',
        'threads': 'string(default=auto)',
    },

    'Languages': {
        'audio': 'force_list(default=list(eng))',
        'subtitle': 'force_list(default=list(eng))'
    },

    'Tagging': {
        'tagfile': 'boolean(default=True)',
        'preferred_show_tagger': 'string(default=tmdb)',
        'preferred_movie_tagger': 'string(default=tmdb)',
        'tag_language': 'string(default=en)',
        'download_artwork': 'boolean(default=False)'
    },

#    'Subtitles': {
#        'download': False,
#        'providers': ['addic7ed', 'podnapisi', 'thesubdb', 'opensubtitles'],
#        'fullpathguess': True
#    },

    'File': {
        'output_directory': 'string(default=None)',
        'copy_to': 'force_list(default=None)',
        'move_to': 'string(default=None)',
        'delete_original': 'boolean(default=False)',
        'permissions': 'integer(default=777)'
    }}

defaultconfig['Containers'] = containersettings
defaultconfig['Codecs'] = codecsettings


configspec = ConfigObj(defaultconfig, list_values=False)

