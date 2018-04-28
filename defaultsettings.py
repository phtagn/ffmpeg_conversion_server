# coding=utf-8
"""
Contains default settings for the app
Settings contain their type to help configparser parse the file correctly
"""

ffmpeg_defaults = {
    'ffmpeg': ('ffmpeg.exe', 'str'),
    'ffprobe': ('ffprobe.exe', 'str'),
    'threads': ('auto', 'strlower'),
    'use_qsv_decoder_with_encoder': (True, 'bool'),
    'use_hevc_qsv_decoder': (False, 'bool'),
    'enable_dxva2_gpu_decode': (False, 'bool')
}
file_defaults = {
    'output_directory': ('', 'str'),
    'copy_to': ('', 'str'),
    'move_to': ('', 'str'),
    'delete_original': (True, 'bool'),
    'permissions': (777, 'int'),
}

program_defaults = {
    'output_extension': ('mp4', 'str'),
    'output_format': ('mp4', 'str'),
}

# Default MP4 conversion settings
mp4_defaults = {
    'relocate_moov': (True, 'bool'),
    'ios_audio': (True, 'bool'),
    'ios_first_track_only': (False, 'bool'),
    'ios_move_last': (False, 'bool'),
    'ios_audio_filter': ('', 'strlower'),
    'max_audio_channels': ('', 'int'),
    'audio_language': ('und', 'strlower'),
    'audio_default_language': ('und', 'str'),
    'audio_codec': ('ac3', 'list'),
    'audio_filter': ('', 'strlower'),
    'audio_channel_bitrate': (256, 'int'),
    'audio_copy_original': (False, 'bool'),
    'video_codec': ('h264, x264', 'list'),
    'preferred_video_codec': ('h264', 'strlower'),
    'video_bitrate': ('', 'float'),
    'video_crf': ('', 'int'),
    'video_max_width': ('', 'int'),
    'video_profile': ('', 'list'),
    'h264_max_level': ('', 'float'),
    'aac_adtstoasc': (False, 'bool'),
    'subtitle_codec': ('mov_text', 'list'),
    'subtitle_language': ('', 'list'),
    'subtitle_default_language': ('', 'strlower'),
    'subtitle_encoding': ('', 'str'),
    'convert_mp4': (False, 'bool'),
    'embed_subs': (True, 'bool'),
    'embed_only_internal_subs': (False, 'bool'),
    'post_process': (False, 'bool'),
    'pix_fmt': ('', 'strlower'),
    'preopts': ('', 'str'),
    'postopts': ('', 'str')
}

subtitle_defaults = {
    'download_subs': (False, 'bool'),
    'sub_providers': ('addic7ed, podnapisi, thesubdb, opensubtitles', 'list'),
    'fullpathguess': ('True', 'bool'),
}

# Default settings for SickBeard
sb_defaults = {'host': ('localhost', 'strlower'),
               'port': ('8081', 'int'),
               'ssl': (False, 'bool'),
               'api_key': ('', 'str'),
               'web_root': ('', 'str'),
               'username': ('', 'str'),
               'password': ('', 'str'),
               'refresh': (False, 'bool')
               }

# Default settings for CouchPotato
cp_defaults = {'host': ('localhost', 'strlower'),
               'port': ('5050', 'int'),
               'username': ('', 'str'),
               'password': ('', 'str'),
               'apikey': ('', 'str'),
               'delay': ('65', 'int'),
               'method': ('renamer', 'str'),
               'delete_failed': (False, 'bool'),
               'ssl': (False, 'bool'),
               'web_root': ('', 'str'),
               'refresh': (False, 'bool')
               }

# Default settings for Sonarr
sonarr_defaults = {'host': ('localhost', 'strlower'),
                   'port': ('8989', 'int'),
                   'apikey': ('', 'str'),
                   'ssl': ('False', 'bool'),
                   'web_root': ('', 'str'),
                   'refresh': (False, 'bool')}

# Default settings for Radarr
radarr_defaults = {'host': ('localhost', 'strlower'),
                   'port': ('7878', 'int'),
                   'apikey': ('', 'str'),
                   'ssl': (False, 'bool'),
                   'web_root': ('', 'str'),
                   'refresh': (False, 'bool')}

# Default uTorrent settings
utorrent_defaults = {'couchpotato_label': ('couchpotato', 'str'),
                     'sickbeard_label': ('sickbeard', 'str'),
                     'sickrage_label': ('sickrage', 'str'),
                     'sonarr_label': ('sonarr', 'str'),
                     'radarr_label': ('radarr', 'str'),
                     'bypass_label': ('bypass', 'str'),
                     'convert': ('True', 'bool'),
                     'webui': ('False', 'bool'),
                     'action_before': ('stop', 'str'),
                     'action_after': ('removedata', 'str'),
                     'host': ('http://localhost:8080/', 'strlower'),
                     'username': ('', 'str'),
                     'password': ('', 'str'),
                     'output_directory': ('', 'str')
                     }
# Default SAB settings
sab_defaults = {'convert': ('True', 'bool'),
                'sickbeard_category': ('sickbeard', 'str'),
                'sickrage_category': ('sickrage', 'str'),
                'couchpotato_category': ('couchpotato', 'str'),
                'sonarr_category': ('sonarr', 'str'),
                'radarr_category': ('radarr', 'str'),
                'bypass_category': ('bypass', 'str'),
                'output_directory': ('', 'str')
                }

# Default Sickrage Settings
sr_defaults = {'host': ('localhost', 'strlower'),
               'port': (8081, 'int'),
               'ssl': (True, 'bool'),
               'api_key': ('', 'str'),
               'web_root': ('', 'str'),
               'username': ('', 'str'),
               'password': ('', 'str'),
               'refresh': (False, 'str')}

# Default deluge settings
deluge_defaults = {'couchpotato_label': ('couchpotato', 'str'),
                   'sickbeard_label': ('sickbeard', 'str'),
                   'sickrage_label': ('sickrage', 'str'),
                   'sonarr_label': ('sonarr', 'str'),
                   'radarr_label': ('radarr', 'str'),
                   'bypass_label': ('bypass', 'str'),
                   'convert': (True, 'bool'),
                   'host': ('localhost', 'strlower'),
                   'port': ('58846', 'int'),
                   'username': ('', 'str'),
                   'password': ('', 'str'),
                   'output_directory': ('', 'str'),
                   'remove': (False, 'bool'),
                   }

# Default Plex Settings
plex_defaults = {'host': ('localhost', 'strlower'),
                 'port': ('32400', 'int'),
                 'token': ('', 'str'),
                 'refresh': (False, 'bool'),
                 }

tag_defaults = {'tagfile': (True, 'bool'),
                'preferred_tv_tagger': ('tvdb', 'strlower'),
                'preferred_movie_tagger': ('tmdb', 'strlower'),
                'tag_language': ('en', 'list'),
                'download_artwork': ('poster', 'strlower')
                }

defaults = {
    'FFMPEG': ffmpeg_defaults,
    'MP4': mp4_defaults,
    'Tagging': tag_defaults,
    'Subtitles': subtitle_defaults,
    'File': file_defaults,
    'SickBeard': sb_defaults,
    'Sickrage': sr_defaults,
    'CouchPotato': cp_defaults,
    'Sonarr': sonarr_defaults,
    'Radarr': radarr_defaults,
    'Plex': plex_defaults,
}
