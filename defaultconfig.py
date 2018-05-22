# coding=utf-8
from containers2 import ContainerFactory
from converter.streamformats import StreamFormatFactory
from converter.avcodecs import CodecFactory
from configobj import ConfigObj


containersettings = {ctn.name: ctn.defaults for ctn in ContainerFactory.containers.values()}

codecsettings = {'video': {cdc.codec_name: cdc.defaults for cdc in CodecFactory.codecs['video'].values()},
                 'audio': {cdc.codec_name: cdc.defaults for cdc in CodecFactory.codecs['audio'].values()},
                 'subtitle': {cdc.codec_name: cdc.defaults for cdc in CodecFactory.codecs['subtitle'].values()}
                 }

formatsettings = {fmt.name: fmt.format_options for fmt in StreamFormatFactory.formats.values()}

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
        'output_directory': 'string(default=None)',
        'copy_to': 'force_list(default=None)',
        'move_to': 'string(default=None)',
        'delete_original': 'boolean(default=False)',
        'permissions': 'integer(default=777)'
    },
    'Containers': containersettings,
    'StreamFormats': formatsettings
}

configspec = ConfigObj(defaultconfig, list_values=False)

