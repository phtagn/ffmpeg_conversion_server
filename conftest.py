# coding=utf-8
from containers import Containers
from converter.avcodecs import audio_codec_dict, video_codec_dict, subtitle_codec_dict

containersettings = dict(zip([ctn.name for ctn in Containers], [ctn.configspecs for ctn in Containers]))
audiocodecs = dict(zip([codec.codec_name for codec in audio_codec_dict.values()],
                       [codec.configspecs for codec in audio_codec_dict.values()]))
videocodecs = dict(zip([codec.codec_name for codec in video_codec_dict.values()],
                       [codec.configspecs for codec in video_codec_dict.values()]))
subtitlecodecs = dict(zip([codec.codec_name for codec in subtitle_codec_dict.values()],
                          [codec.configspecs for codec in subtitle_codec_dict.values()]))
del audiocodecs['copy']
del videocodecs['copy']
del subtitlecodecs['copy']

configdict = {
    'FFMPEG': {
        'ffmpeg': 'string(default=/usr/local/bin/ffmpeg)',
        'ffprobe': 'string(default=/usr/local/bin/ffprobe)',
        'threads': 'string()',
        'use_qsv_decoder_with_encoder': 'boolean(default=True)',
        'use_hevc_qsv_decoder': 'boolean(default=False)'
    },

    'Languages': {
        'audio': 'string_list(default=list(eng))',
        'subtitle': 'string_list(default=list(eng))'
    },

    'Tagging': {
        'tagfile': 'boolean(default=True)',
        'preferred_tv_tagger': 'string(default=tvdb)',
        'preferred_movie_tagger': 'string(default=tmdb)',
        'tag_language': 'string(default=en)',
        'download_artwork': 'string(default=poster)'
    },

    'Subtitles': {
        'download': 'boolean(default=False)',
        'providers': 'list(default=list(addic7ed, podnapisi, thesubdb, opensubtitles))',
        'fullpathguess': 'boolean(default=True)'
    },

    'File': {
        'output_directory': 'string()',
        'copy_to': 'string()',
        'move_to': 'string()',
        'delete_original': 'boolean(default=False)',
        'permissions': 'integer(default=777)'
    }}

configdict['Containers'] = containersettings
configdict['Codecs'] = {'Video': videocodecs, 'Audio': audiocodecs, 'Subtitle': subtitlecodecs}
