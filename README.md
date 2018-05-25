Conversion/Tagging Server.
==============

**Automatically converts, tags and moves video files**

Works on Windows, OSX, and Linux

Requirements
--------------
- Python 3.6
TODO

Default Settings
--------------
TODO

Prerequisite PIP Package Installation Instructions
--------------
Note: Windows users should enter commands in Powershell - using '<' doesn't work in cmd
- `VC for Python 2.7` (Windows Users Only) - Download and install - http://www.microsoft.com/en-us/download/details.aspx?id=44266
- `setuptools` - https://pypi.python.org/pypi/setuptools#installation-instructions
- `requests` - Run `pip install requests`
- `requests security package` - Run `pip install requests[security]`
- `requests-cache` - Run `pip install requests-cache`
- `babelfish` - Run `pip install babelfish`
- `Flask`- Run `pip install flask`
- Optional: `qtfaststart` Run `pip install qtfaststart` to enable moving moov atom

How it works
--------------
The server is supplied with e default configuration file called user.ini. You can edit this configuration file to suit your needs.
The server supports multiple configuration files. In other words, a request to the server may contain the name of a specific configuration file, that is then loaded on demand.
This enables you to have different behaviour.

Configuration
--------------
The default configuration file is split into different sections:

[FFMPEG] Sets the details for ffmpeg
- `ffmpeg` : the path to ffmpeg binary
- `fprobe`: the path to ffprobe binary
- `threads`: either auto or the number of threads you wish ffmpeg to use. Note that not all encoders support multi-threading.

[Languages] Setttings for the languages you want in the file:
- `audio`: a comma separated list of 3-letter language code. Those are all the languages that are acceptable to you. Any audio track whose language does not match will be disregarded.
- `subtitle`: same for subtitles

[Tagging] Settings for tagging. *At the moment tagging is only supported for MP4.*
- `tagfile`: `True` or `False` whether you want the file to be tagged
- `preferred_show_tagger`: the source you prefer using when tagging TV shows. At the moment tvdb and tmdb only are supported.
- `preferred_movie_tagger`: the source you prefer using when tagging movie files. Only tmdb is supported at the moment.
- `tag_language`: a 2-letter code for the language you want to use for tagging
- `download_artwork`: `True` or `False` to add the artwork to the file

[Containers] Settings for supported containers. *At the moment, only MKV and MP4 are supported*
- `prefer_method`: Applies to video stream only. Valid values are `copy`, `transcode`, and `override`.
    - Copy will copy the video stream everytime if the codec of the video stream is in the `video_codecs` list
    - Transcode will transcode the video stream everytime, using the codec provided in `transcode_with`
    - Override is a little more complicated and designed to be versatile. Override will first look at whether the codec
    is listed in the accepted codecs. If it is, it will check that the format conforms with the options as set out in the
    appropriate subsection of the StreamFormat section. 
    
    The difference with copy is that copy only matches the format (i.e. if the format of the video track is h264 and h264 is listed in accepted_formats then copying will occur. If not transcoding will. 
    If override is selected the, the program will also check e.g. that the video bitrate is below the video bitrate accepted for the codec.
    The reason why this is not folded into copy is that you may want a max bitrate of 2000k for h264 and 1500 for h265.    
- `video_codecs`: A *list* of the video codecs that are acceptable to be included in the output file. If the codec of the source file is not included in this list, then transcoding will occur using the `transcode_with`codec.
- `transcode_with`: the codec with which you want to transcode. All supported codecs are listed in the [Codecs] section.
- `audio_codecs`: A *list* of the audio codecs that can be included in the output file. Those codecs will be copied (provided the language matches).
- `audio_create_streams`: a *list* of audio streams you want created.
Examples:
1. If the source file has audio in ac3, and you have specified `audio_codecs` = ac3 and `audio_create_streams` = aac, mp3, then (a) the ac3 stream will be copied, (b) an aac stream will be created and (c) an mp3 stream will be created. This applies to each audio stream.
2. If the source file has audio in dts, and you have specified `audio_codecs` = ac3 and `audio_create_streams` = aac, mp3, then (a) an aac stream will be created and (b) an mp3 stream will be created. This applies to each audio stream. 
- `audio_copy_original`: will copy the original audio stream even if it is not in the `audio_codecs`setting.
- `subtitle_codecs`: a *list* of acceptable subtitle codecs.
- `process_same`: `True` or `False` if True then conversion from mkv to mkv or mp4 to mp4 will occur, otherwise only conversion from mkv to mp4 or mp4 to mkv will occur.
- `preopts`: Additional unsupported options that go before the rest of the FFMPEG parameters, comma separated (Example `-preset,medium`)
- `postopts`: Additional unsupported options that go after the rest of the FFMEPG parameters, comma separated as above
- `pix_fmts`: a *list* of pix formats that are acceptable. If the source file pix format is not included in the list, and `prefer_method`is set to override, transcoding will occur. If None, all pix formats are OK.
- `profiles`: **For codecs that support it (e.g. h264 and h265)**, a *list* of profiles that are acceptable. If the source file profile is not included in the list, and `prefer_method`is set to override, transcoding will occur. If None, all profiles are OK.

**MP4 only options**
- `relocate_moov`: True/False - relocates the MOOV atom to the beginning of the file for better streaming.

[Codecs]
Supported options for codecs. Those options are used when the codec is used for transcoding. They are also used in the override method to determine whether the stream should be copied.
They are mostly self explanatory for each codec. Note that when used with the override method, those are maximum values, i.e. if the source file's value for width is bigger than the codec's the file will be transcoded.
If a value is None, then it is not used in the comparison.

Building clients (API)
----------------------

TODO.



