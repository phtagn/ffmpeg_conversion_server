# coding=utf-8
from converter.streamformats import StreamFormatFactory
from converter.encoders import EncoderFactory
from refreshers.refreshers import RefresherFactory
from configobj import ConfigObj


#containersettings = {ctn.name: ctn.defaults for ctn in SourceContainerFactory.containers.values()}

generic_container_settings = {
        'video': {
            'accepted_track_formats': 'force_list(default=list(h264, h265, hevc))',
            'prefer_method': 'option(copy, transcode, override, default=copy)',
            'transcode_to': 'string(default=h264)'
        },

        'audio': {
            'accepted_track_formats': 'force_list(default=list(aac, ac3))',
            'audio_copy_original': 'boolean(default=False)',
            'create_multiple_stereo_tracks': 'boolean(default=False)',
            'force_create_tracks': 'force_list(default=None)',
            'transcode_to': 'string(default=aac)',
        },

        'subtitle': {
            'accepted_track_formats': 'force_list(default=list(mov_text))',
            'transcode_to': 'string(default=mov_text)'
        },

        'post_processors': 'force_list(default=None)',
        'preopts': 'string(default=None)',
        'postopts': 'string(default=None)'
    }

supported_containers = ['mp4', 'mkv']

containersettings = {supported_container: generic_container_settings for supported_container in supported_containers}


encosettings = {cdc.codec_name: cdc.defaults for cdc in EncoderFactory.codecs['video'].values() if cdc.defaults}
encosettings.update({cdc.codec_name: cdc.defaults for cdc in EncoderFactory.codecs['audio'].values() if cdc.defaults})
encosettings.update({cdc.codec_name: cdc.defaults for cdc in EncoderFactory.codecs['subtitle'].values() if cdc.defaults})


formatsettings = {fmt.name: fmt.format_options for fmt in StreamFormatFactory.formats.values()}

refreshersettings = {refresher.name: refresher.defaults for refresher in RefresherFactory.Refreshers.values()}
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
        'copy_to': 'force_list(default=None)',
        'move_to': 'string(default=None)',
        'delete_original': 'boolean(default=False)',
        'permissions': 'integer(default=777)'
    },
    'Containers': containersettings,
    'TrackFormats': formatsettings,
    'Encoders': encosettings,
    'Refreshers': refreshersettings
}


configspec = ConfigObj(defaultconfig, list_values=False)

