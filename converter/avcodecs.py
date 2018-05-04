#!/usr/bin/env python
from typing import Dict, Union


class BaseCodec(object):
    """
    Base audio/video codec class.
    """
    configspecs = {}
    encoder_options = {}
    codec_name = None
    ffmpeg_codec_name = None

    def __init__(self):

        self.__safeopts = {}

    @property
    def safeopts(self):
        return self.__safeopts

    def parse_options(self, opt: Dict[str, Union[str, int]]):
        return None

    def _codec_specific_parse_options(self, safe: Dict[str, Union[str, int]]):
        return safe

    def _codec_specific_produce_ffmpeg_list(self, safe: Dict[str, Union[str, int]], stream: int = 0):
        return []

    def add_options(self, opts: Dict[str, Union[str, int]]) -> None:

        # Only copy options that are expected and of correct type
        # (and do typecasting on them)
        for k, v in opts.items():
            if k in self.encoder_options and v is not None and v is not '':
                typ = self.encoder_options[k]
                try:
                    self.__safeopts[k] = typ(v)
                except:
                    pass


class AudioCodec(BaseCodec):
    """
    Base audio codec class handles general audio options. Possible
    parameters are:
      * codec (string) - audio codec name
      * channels (integer) - number of audio channels
      * bitrate (integer) - stream bitrate
      * samplerate (integer) - sample rate (frequency)
      * language (str) - language of audio stream (3 char code)
      * map (int) - stream index

    Supported audio codecs are: null (no audio), copy (copy from
    original), vorbis, aac, mp3, mp2
    """
    codec_type = 'audio'
    encoder_options = {
        'codec': str,
        'language': str,
        'channels': int,
        'bitrate': int,
        'samplerate': int,
        'source': int,
        'path': str,
        'filter': str,
        'map': int,
        'disposition': str,
    }
    configspecs = {
        'channels': 'integer(1, 6, default=6)',
        'bitrate': 'integer(8, 1536, default=None)',
        'filter': 'string(default=None)'
    }
    def parse_options(self, opt, stream=0):
        # super(AudioCodec, self).parse_options(opt)
        # safe = self.safe_options(opt)
        safe = self.safeopts
        stream = str(stream)

        if 'channels' in safe:
            c = safe['channels']
            if c < 1 or c > 12:
                del safe['channels']

        if 'bitrate' in safe:
            br = safe['bitrate']
            if br < 8:
                br = 8
            if br > 1536:
                br = 1536

        if 'samplerate' in safe:
            f = safe['samplerate']
            if f < 1000 or f > 50000:
                del safe['samplerate']

        if 'language' in safe:
            l = safe['language']
            if len(l) > 3:
                del safe['language']

        if 'source' in safe:
            s = str(safe['source'])
        else:
            s = str(0)

        if 'filter' in safe:
            x = safe['filter']
            if len(x) < 1:
                del safe['filter']

        safe = self._codec_specific_parse_options(safe)
        optlist = []
        optlist.extend(['-c:a:' + stream, self.ffmpeg_codec_name])
        if 'path' in safe:
            optlist.extend(['-i', str(safe['path'])])
        if 'map' in safe:
            optlist.extend(['-map', s + ':' + str(safe['map'])])
        if 'disposition' in safe:
            optlist.extend(['-disposition:a:' + stream, str(safe['disposition'])])
        if 'channels' in safe:
            optlist.extend(['-ac:a:' + stream, str(safe['channels'])])
        if 'bitrate' in safe:
            optlist.extend(['-b:a:' + stream, str(br) + 'k'])
        if 'samplerate' in safe:
            optlist.extend(['-ar:a:' + stream, str(safe['samplerate'])])
        if 'filter' in safe:
            optlist.extend(['-filter:a:' + stream, str(safe['filter'])])
        if 'language' in safe:
            lang = str(safe['language'])
        else:
            lang = 'und'  # Never leave blank if not specified, always set to und for undefined
        optlist.extend(['-metadata:s:a:' + stream, "language=" + lang])

        optlist.extend(self._codec_specific_produce_ffmpeg_list(safe))
        return optlist


class SubtitleCodec(BaseCodec):
    """
    Base subtitle codec class handles general subtitle options. Possible
    parameters are:
      * codec (string) - subtitle codec name (mov_text, subrib, ssa only supported currently)
      * language (string) - language of subtitle stream (3 char code)
      * forced (int) - force subtitles (1 true, 0 false)
      * default (int) - default subtitles (1 true, 0 false)

    Supported subtitle codecs are: null (no subtitle), mov_text
    """
    codec_type = 'subtitle'
    encoder_options = {
        'codec': str,
        'language': str,
        'forced': int,
        'default': int,
        'map': int,
        'source': int,
        'path': str,
        'encoding': str
    }

    configspecs = {'encoding': 'string(default=UTF8)'}

    def parse_options(self, opt, stream=0):
        #super(SubtitleCodec, self).parse_options(opt)
        stream = str(stream)
        safe = self.safeopts

        if 'forced' in safe:
            f = safe['forced']
            if f < 0 or f > 1:
                del safe['forced']

        if 'default' in safe:
            d = safe['default']
            if d < 0 or d > 1:
                del safe['default']

        if 'language' in safe:
            l = safe['language']
            if len(l) > 3:
                del safe['language']

        if 'source' in safe:
            s = str(safe['source'])
        else:
            s = str(0)

        if 'encoding' in safe:
            if not safe['encoding']:
                del safe['encoding']

        safe = self._codec_specific_parse_options(safe)

        optlist = []
        if 'encoding' in safe:
            optlist.extend(['-sub_charenc', str(safe['encoding'])])
        optlist.extend(['-c:s:' + stream, self.ffmpeg_codec_name])

        if 'map' in safe:
            optlist.extend(['-map', s + ':' + str(safe['map'])])
        if 'path' in safe:
            optlist.extend(['-i', str(safe['path'])])
        if 'default' in safe:
            optlist.extend(['-metadata:s:s:' + stream, "disposition:default=" + str(safe['default'])])
        if 'forced' in safe:
            optlist.extend(['-metadata:s:s:' + stream, "disposition:forced=" + str(safe['forced'])])
        if 'language' in safe:
            lang = str(safe['language'])
        else:
            lang = 'und'  # Never leave blank if not specified, always set to und for undefined
        optlist.extend(['-metadata:s:s:' + stream, "language=" + lang])

        optlist.extend(self._codec_specific_produce_ffmpeg_list(safe))
        return optlist


class VideoCodec(BaseCodec):
    """
    Base video codec class handles general video options. Possible
    parameters are:
      * codec (string) - video codec name
      * bitrate (string) - stream bitrate
      * fps (integer) - frames per second
      * width (integer) - video width
      * height (integer) - video height
      * mode (string) - aspect preserval mode; one of:
            * stretch (default) - don't preserve aspect
            * crop - crop extra w/h
            * pad - pad with black bars
      * src_width (int) - source width
      * src_height (int) - source height

    Aspect preserval mode is only used if both source
    and both destination sizes are specified. If source
    dimensions are not specified, aspect settings are ignored.

    If source dimensions are specified, and only one
    of the destination dimensions is specified, the other one
    is calculated to preserve the aspect ratio.

    Supported video codecs are: null (no video), copy (copy directly
    from the source), Theora, H.264/AVC, DivX, VP8, H.263, Flv,
    MPEG-1, MPEG-2.
    """
    codec_type = 'video'
    encoder_options = {
        'codec': str,
        'bitrate': int,
        'crf': int,
        'fps': int,
        'width': int,
        'height': int,
        'mode': str,
        'src_width': int,
        'src_height': int,
        'filter': str,
        'pix_fmt': str,
        'map': int
    }

    configspecs = {
        'bitrate': 'integer(default=None)',
        'max_width': 'integer(defaul=None)',
        'filter': 'string(default=None)',
        'pix_fmt': 'list(default=None)'
    }

    def _aspect_corrections(self, sw, sh, w, h, mode):
        # If we don't have source info, we don't try to calculate
        # aspect corrections
        if not sw or not sh:
            return w, h, None

        # Original aspect ratio
        aspect = (1.0 * sw) / (1.0 * sh)

        # If we have only one dimension, we can easily calculate
        # the other to match the source aspect ratio
        if not w and not h:
            return w, h, None
        elif w and not h:
            h = int((1.0 * w) / aspect)
            return w, h, None
        elif h and not w:
            w = int(aspect * h)
            return w, h, None

        # If source and target dimensions are actually the same aspect
        # ratio, we've got nothing to do
        if int(aspect * h) == w:
            return w, h, None

        if mode == 'stretch':
            return w, h, None

        target_aspect = (1.0 * w) / (1.0 * h)

        if mode == 'crop':
            # source is taller, need to crop top/bottom
            if target_aspect > aspect:  # target is taller
                h0 = int(w / aspect)
                assert h0 > h, (sw, sh, w, h)
                dh = (h0 - h) / 2
                return w, h0, 'crop=%d:%d:0:%d' % (w, h, dh)
            else:  # source is wider, need to crop left/right
                w0 = int(h * aspect)
                assert w0 > w, (sw, sh, w, h)
                dw = (w0 - w) / 2
                return w0, h, 'crop=%d:%d:%d:0' % (w, h, dw)

        if mode == 'pad':
            # target is taller, need to pad top/bottom
            if target_aspect < aspect:
                h1 = int(w / aspect)
                assert h1 < h, (sw, sh, w, h)
                dh = (h - h1) / 2
                return w, h1, 'pad=%d:%d:0:%d' % (w, h, dh)  # FIXED
            else:  # target is wider, need to pad left/right
                w1 = int(h * aspect)
                assert w1 < w, (sw, sh, w, h)
                dw = (w - w1) / 2
                return w1, h, 'pad=%d:%d:%d:0' % (w, h, dw)  # FIXED

        assert False, mode

    def parse_options(self, opt, stream=0):
        super(VideoCodec, self).parse_options(opt)
        stream = str(stream)
        safe = self.safeopts

        if 'fps' in safe:
            f = safe['fps']
            if f < 1 or f > 120:
                del safe['fps']

        if 'bitrate' in safe:
            br = safe['bitrate']
            if br < 16 or br > 15000:
                del safe['bitrate']

        if 'crf' in safe:
            crf = safe['crf']
            if crf < 0 or crf > 51:
                del safe['crf']

        w = None
        h = None

        if 'width' in safe:
            w = safe['width']
            if w < 16 or w > 4000:
                w = None

        if 'height' in safe:
            h = safe['height']
            if h < 16 or h > 3000:
                h = None

        sw = None
        sh = None

        if 'src_width' in safe and 'src_height' in safe:
            sw = safe['src_width']
            sh = safe['src_height']
            if not sw or not sh:
                sw = None
                sh = None

        mode = 'stretch'
        if 'mode' in safe:
            if safe['mode'] in ['stretch', 'crop', 'pad']:
                mode = safe['mode']

        ow, oh = w, h  # FIXED
        w, h, filters = self._aspect_corrections(sw, sh, w, h, mode)

        safe['width'] = w
        safe['height'] = h
        safe['aspect_filters'] = filters

        if w and h:
            safe['aspect'] = '%d:%d' % (w, h)

        safe = self._codec_specific_parse_options(safe)

        w = safe['width']
        h = safe['height']
        filters = safe['aspect_filters']

        optlist = ['-vcodec', self.ffmpeg_codec_name]
        if 'map' in safe:
            optlist.extend(['-map', '0:' + str(safe['map'])])
        if 'fps' in safe:
            optlist.extend(['-r', str(safe['fps'])])
        if 'pix_fmt' in safe:
            optlist.extend(['-pix_fmt', str(safe['pix_fmt'])])
        if 'bitrate' in safe:
            optlist.extend(['-vb', str(br) + 'k'])  # FIXED
        if 'crf' in safe:
            optlist.extend(['-crf', str(safe['crf'])])
        if 'filter' in safe:
            if filters:
                filters = '%s;%s' % (filters, str(safe['filter']))
            else:
                filters = str(safe['filter'])
        if w and h:
            optlist.extend(['-s', '%dx%d' % (w, h)])

            if ow and oh:
                optlist.extend(['-aspect', '%d:%d' % (ow, oh)])

        if filters:
            optlist.extend(['-vf', filters])

        optlist.extend(self._codec_specific_produce_ffmpeg_list(safe))

        if optlist.count('-vf') > 1:
            vf = []
            while optlist.count('-vf') > 0:
                vf.append(optlist.pop(optlist.index('-vf') + 1))
                del optlist[optlist.index('-vf')]

            vfstring = ""
            for line in vf:
                vfstring = "%s;%s" % (vfstring, line)

            optlist.extend(['-vf', vfstring[1:]])

        return optlist


class AudioNullCodec(BaseCodec):
    """
    Null audio codec (no audio).
    """
    codec_name = None
    codec_type = 'audio'

    def parse_options(self, opt, stream=0):
        return ['-an']


class VideoNullCodec(BaseCodec):
    """
    Null video codec (no video).
    """

    codec_name = None
    codec_type = 'video'

    def parse_options(self, opt):
        return ['-vn']


class SubtitleNullCodec(BaseCodec):
    """
    Null subtitle codec (no subtitle)
    """

    codec_name = None
    codec_type = 'subtitle'

    def parse_options(self, opt, stream=0):
        return ['-sn']


class AudioCopyCodec(BaseCodec):
    """
    Copy audio stream directly from the source.
    """
    codec_name = 'copy'
    codec_type = 'audio'
    encoder_options = {'language': str,
                       'source': str,
                       'map': int,
                       'bsf': str,
                       'disposition': str}

    def __init__(self) -> None:
        super(self.__class__, self).__init__()

    def parse_options(self, opt, stream=0):
        #        safe = self.safe_options(opt)
        safe = self.safeopts
        stream = str(stream)
        optlist = []
        optlist.extend(['-c:a:' + stream, 'copy'])
        if 'source' in safe:
            s = str(safe['source'])
        else:
            s = str(0)
        if 'map' in safe:
            optlist.extend(['-map', s + ':' + str(safe['map'])])
        if 'bsf' in safe:
            optlist.extend(['-bsf:a:' + stream, str(safe['bsf'])])
        lang = 'und'
        if 'language' in safe:
            l = safe['language']
            if len(l) > 3:
                del safe['language']
            else:
                lang = str(safe['language'])
        optlist.extend(['-metadata:s:a:' + stream, "language=" + lang])
        if 'disposition' in safe:
            optlist.extend(['-disposition:a:' + stream, str(safe['disposition'])])
        return optlist


class VideoCopyCodec(BaseCodec):
    """
    Copy video stream directly from the source.
    """

    def __init__(self) -> None:
        super(self.__class__, self).__init__()

    codec_name = 'copy'
    codec_type = 'video'
    encoder_options = {'map': int,
                       'source': str}

    def parse_options(self, opt, stream=0):
        #        safe = self.safe_options(opt)
        safe = self.safeopts
        optlist = []
        optlist.extend(['-vcodec', 'copy'])
        if 'source' in safe:
            s = str(safe['source'])
        else:
            s = str(0)
        if 'map' in safe:
            optlist.extend(['-map', s + ':' + str(safe['map'])])
        return optlist


class SubtitleCopyCodec(BaseCodec):
    """
    Copy subtitle stream directly from the source.
    """
    codec_name = 'copy'
    codec_type = 'subtitle'
    encoder_options = {'map': int,
                       'source': str}

    def __init__(self) -> None:
        super(self.__class__, self).__init__()

    def parse_options(self, opt, stream=0):
        optlist = []
        # safe = self.safe_options(opt)
        safe = self.safeopts
        stream = str(stream)
        if 'source' in safe:
            s = str(safe['source'])
        else:
            s = str(0)
        if 'map' in safe:
            optlist.extend(['-map', s + ':' + str(safe['map'])])
        optlist.extend(['-c:s:' + stream, 'copy'])
        return optlist


# Audio Codecs
class VorbisCodec(AudioCodec):
    """
    Vorbis audio codec.
    """

    def __init__(self) -> None:
        super(self.__class__, self).__init__()

    codec_name = 'vorbis'
    ffmpeg_codec_name = 'libvorbis'
    encoder_options = AudioCodec.encoder_options.copy()
    encoder_options.update({
        'quality': int,  # audio quality. Range is 0-10(highest quality)
        # 3-6 is a good range to try. Default is 3
    })
    configspecs = AudioCodec.configspecs.copy()
    configspecs.update({'quality': 'integer(0, 10, default=3)'})

    def _codec_specific_produce_ffmpeg_list(self, safe, stream=0):
        optlist = []
        stream = str(stream)
        if 'quality' in safe:
            optlist.extend(['-qscale:a:' + stream, safe['quality']])
        return optlist


class AacCodec(AudioCodec):
    """
    AAC audio codec.
    """
    codec_name = 'aac'
    ffmpeg_codec_name = 'aac'

    def __init__(self) -> None:
        super(self.__class__, self).__init__()

    def parse_options(self, opt, stream=0):
        if 'channels' in opt:
            c = opt['channels']
            if c > 6:
                opt['channels'] = 6
        return super(AacCodec, self).parse_options(opt, stream)

    def _codec_specific_produce_ffmpeg_list(self, safe, stream=0):
        return safe


class FdkAacCodec(AudioCodec):
    """
    AAC audio codec.
    """
    codec_name = 'libfdk_aac'
    ffmpeg_codec_name = 'libfdk_aac'

    def __init__(self) -> None:
        super(self.__class__, self).__init__()

    def parse_options(self, opt, stream=0):
        if 'channels' in opt:
            c = opt['channels']
            if c > 6:
                opt['channels'] = 6
        return super(FdkAacCodec, self).parse_options(opt, stream)


class FAacCodec(AudioCodec):
    """
    AAC audio codec.
    """
    codec_name = 'libfaac'
    ffmpeg_codec_name = 'libfaac'

    def __init__(self) -> None:
        super(self.__class__, self).__init__()

    def parse_options(self, opt, stream=0):
        if 'channels' in opt:
            c = opt['channels']
            if c > 6:
                opt['channels'] = 6
        return super(FAacCodec, self).parse_options(opt, stream)


class Ac3Codec(AudioCodec):
    """
    AC3 audio codec.
    """
    codec_name = 'ac3'
    ffmpeg_codec_name = 'ac3'

    def __init__(self) -> None:
        super(self.__class__, self).__init__()

    def parse_options(self, opt, stream=0):
        if 'channels' in opt:
            c = opt['channels']
            if c > 6:
                opt['channels'] = 6
        return super(Ac3Codec, self).parse_options(opt, stream)

class EAc3Codec(AudioCodec):
    """
    Dolby Digital Plus/EAC3 audio codec.
    """
    codec_name = 'eac3'
    ffmpeg_codec_name = 'eac3'

    def __init__(self) -> None:
        super(self.__class__, self).__init__()

    def parse_options(self, opt, stream=0):
        if 'channels' in opt:
            c = opt['channels']
            if c > 8:
                opt['channels'] = 8
        if 'bitrate' in opt:
            br = opt['bitrate']
            if br > 640:
                opt['bitrate'] = 640
        return super(EAc3Codec, self).parse_options(opt, stream)


class FlacCodec(AudioCodec):
    """
    FLAC audio codec.
    """
    codec_name = 'flac'
    ffmpeg_codec_name = 'flac'
    flac_experimental_enable = ['-strict', 'experimental']

    def __init__(self) -> None:
        super(self.__class__, self).__init__()

    def _codec_specific_produce_ffmpeg_list(self, safe, stream=0):
        return self.flac_experimental_enable


class DtsCodec(AudioCodec):
    """
    DTS audio codec.
    """
    codec_name = 'dts'
    ffmpeg_codec_name = 'dts'

    def __init__(self) -> None:
        super(self.__class__, self).__init__()

class Mp3Codec(AudioCodec):
    """
    MP3 (MPEG layer 3) audio codec.
    """
    codec_name = 'mp3'
    ffmpeg_codec_name = 'libmp3lame'

    def __init__(self) -> None:
        super(self.__class__, self).__init__()

class Mp2Codec(AudioCodec):
    """
    MP2 (MPEG layer 2) audio codec.
    """
    codec_name = 'mp2'
    ffmpeg_codec_name = 'mp2'

    def __init__(self) -> None:
        super(self.__class__, self).__init__()

# Video Codecs
class TheoraCodec(VideoCodec):
    """
    Theora video codec.
    """
    codec_name = 'theora'
    ffmpeg_codec_name = 'libtheora'
    encoder_options = VideoCodec.encoder_options.copy()
    encoder_options.update({
        'quality': int,  # audio quality. Range is 0-10(highest quality)
        # 5-7 is a good range to try (default is 200k bitrate)
    })
    configspecs = VideoCopyCodec.configspecs.copy()
    configspecs.update({'quality': 'integer(0, 10, default=None)'})

    def __init__(self) -> None:
        super(self.__class__, self).__init__()

    def _codec_specific_produce_ffmpeg_list(self, safe, stream=0):
        optlist = []
        if 'quality' in safe:
            optlist.extend(['-qscale:v', safe['quality']])
        return optlist


class H264Codec(VideoCodec):
    """
    H.264/AVC video codec.
    """
    codec_name = 'h264'
    ffmpeg_codec_name = 'libx264'
    encoder_options = VideoCodec.encoder_options.copy()
    encoder_options.update({
        'preset': str,  # common presets are ultrafast, superfast, veryfast,
        # faster, fast, medium(default), slow, slower, veryslow
        'quality': int,  # constant rate factor, range:0(lossless)-51(worst)
        # default:23, recommended: 18-28
        'profile': str,  # default: not-set, for valid values see above link
        'level': float,  # default: not-set, values range from 3.0 to 4.2
        'tune': str,  # default: not-set, for valid values see above link
        'wscale': int,  # special handlers for the even number requirements of h264
        'hscale': int  # special handlers for the even number requirements of h264
    })
    configspecs = VideoCodec.configspecs.copy()
    configspecs.update({'preset': 'string(default=None)',
                        'quality': 'integer(0, 51, default=23)',
                        'profile': 'string(default=None)',
                        'level': 'float(default=None)',
                        'tune': 'string(default=None)'
                        })

    def __init__(self) -> None:
        super(self.__class__, self).__init__()

    def parse_options(self, opt, stream=0):
        if 'width' in opt:
            opt['wscale'] = opt['width']
            del(opt['width'])
        if 'height' in opt:
            opt['hscale'] = opt['height']
            del(opt['height'])
        return super(H264Codec, self).parse_options(opt, stream)

    def _codec_specific_produce_ffmpeg_list(self, safe, stream=0):
        optlist = []
        if 'level' in safe:
            if safe['level'] < 3.0 or safe['level'] > 4.2:
                del safe['level']

        if 'preset' in safe:
            optlist.extend(['-preset', safe['preset']])
        if 'quality' in safe:
            optlist.extend(['-crf', str(safe['quality'])])
        if 'profile' in safe:
            optlist.extend(['-profile:v', safe['profile']])
        if 'level' in safe:
            optlist.extend(['-level', '%0.1f' % safe['level']])
        if 'tune' in safe:
            optlist.extend(['-tune', safe['tune']])
        if 'wscale' in safe and 'hscale' in safe:
            optlist.extend(['-vf', 'scale=%s:%s' % (safe['wscale'], safe['hscale'])])
        elif 'wscale' in safe:
            optlist.extend(['-vf', 'scale=%s:trunc(ow/a/2)*2' % (safe['wscale'])])
        elif 'hscale' in safe:
            optlist.extend(['-vf', 'scale=trunc((oh*a)/2)*2:%s' % (safe['hscale'])])
        return optlist


class X264(H264Codec):
    """
    Alias for H264
    """
    codec_name = 'x264'

    def __init__(self) -> None:
        super(self.__class__, self).__init__()

class NVEncH264(H264Codec):
    """
    Nvidia H.264/AVC video codec.
    """
    codec_name = 'nvenc_h264'
    ffmpeg_codec_name = 'nvenc_h264'

    def __init__(self) -> None:
        super(self.__class__, self).__init__()

class H264VAAPI(H264Codec):
    """
    H.264/AVC video codec.
    """
    codec_name = 'h264vaapi'
    ffmpeg_codec_name = 'h264_vaapi'

    def __init__(self) -> None:
        super(self.__class__, self).__init__()

    def _codec_specific_produce_ffmpeg_list(self, safe, stream=0):
        optlist = []
        optlist.extend(['-vaapi_device', '/dev/dri/renderD128'])
        if 'preset' in safe:
            optlist.extend(['-preset', safe['preset']])
        if 'quality' in safe:
            optlist.extend(['-crf', str(safe['quality'])])
        if 'profile' in safe:
            optlist.extend(['-profile:v', safe['profile']])
        if 'level' in safe:
            optlist.extend(['-level', '%0.0f' % (safe['level'] * 10)])  # Automatically multiplied by 10
        if 'tune' in safe:
            optlist.extend(['-tune', safe['tune']])
        # Start VF
        optlist.extend(['-vf', "format=nv12,hwupload"])
        if 'wscale' in safe and 'hscale' in safe:
            optlist.extend(['-vf', 'scale=%s:%s' % (safe['wscale'], safe['hscale'])])
        elif 'wscale' in safe:
            optlist.extend(['-vf', 'scale=%s:trunc(ow/a/2)*2' % (safe['wscale'])])
        elif 'hscale' in safe:
            optlist.extend(['-vf', 'scale=trunc((oh*a)/2)*2:%s' % (safe['hscale'])])
        return optlist


class H264QSV(H264Codec):
    """
    H.264/AVC video codec.
    """
    codec_name = 'h264qsv'
    ffmpeg_codec_name = 'h264_qsv'

    def __init__(self) -> None:
        super(self.__class__, self).__init__()

    def _codec_specific_produce_ffmpeg_list(self, safe, stream=0):
        optlist = []
        optlist.extend(['-look_ahead', '0'])
        return optlist


class H265Codec(VideoCodec):
    """
    H.265/AVC video codec.
    """
    codec_name = 'h265'
    ffmpeg_codec_name = 'libx265'
    encoder_options = VideoCodec.encoder_options.copy()
    encoder_options.update({
        'preset': str,  # common presets are ultrafast, superfast, veryfast,
        # faster, fast, medium(default), slow, slower, veryslow
        'quality': int,  # constant rate factor, range:0(lossless)-51(worst)
        # default:23, recommended: 18-28
        'profile': str,  # default: not-set, for valid values see above link
        'level': float,  # default: not-set, values range from 3.0 to 4.2
        'tune': str,  # default: not-set, for valid values see above link
        'wscale': int,  # special handlers for the even number requirements of h265
        'hscale': int  # special handlers for the even number requirements of h265
    })

    configspecs = VideoCodec.configspecs.copy()
    configspecs.update({'preset': 'string(default=None',
                        'quality': 'integer(0, 51, default=23)',
                        'profile': 'string(default=None)',
                        'level': 'float(default=0.0)',
                        'tune': 'string(default=None)'
                        })

    def __init__(self) -> None:
        super(self.__class__, self).__init__()

    def parse_options(self, opt, stream=0):
        if 'width' in opt:
            opt['wscale'] = opt['width']
            del(opt['width'])
        if 'height' in opt:
            opt['hscale'] = opt['height']
            del(opt['height'])
        return super(H265Codec, self).parse_options(opt, stream)

    def _codec_specific_produce_ffmpeg_list(self, safe, stream=0):
        optlist = []

        if 'preset' in safe:
            optlist.extend(['-preset', safe['preset']])
        if 'quality' in safe:
            optlist.extend(['-crf', str(safe['quality'])])
        if 'profile' in safe:
            optlist.extend(['-profile:v', safe['profile']])
        if 'level' in safe:
            optlist.extend(['-level', '%0.1f' % safe['level']])
        if 'tune' in safe:
            optlist.extend(['-tune', safe['tune']])
        if 'wscale' in safe and 'hscale' in safe:
            optlist.extend(['-vf', 'scale=%s:%s' % (safe['wscale'], safe['hscale'])])
        elif 'wscale' in safe:
            optlist.extend(['-vf', 'scale=%s:trunc(ow/a/2)*2' % (safe['wscale'])])
        elif 'hscale' in safe:
            optlist.extend(['-vf', 'scale=trunc((oh*a)/2)*2:%s' % (safe['hscale'])])
        optlist.extend(['-tag:v', 'hvc1'])
        return optlist


class HEVCQSV(H265Codec):
    """
    HEVC video codec.
    """
    codec_name = 'hevcqsv'
    ffmpeg_codec_name = 'hevc_qsv'

    def __init__(self) -> None:
        super(self.__class__, self).__init__()


class NVEncH265(H265Codec):
    """
    Nvidia H.265/AVC video codec.
    """
    codec_name = 'nvenc_h265'
    ffmpeg_codec_name = 'hevc_nvenc'

    def __init__(self) -> None:
        super(self.__class__, self).__init__()


class DivxCodec(VideoCodec):
    """
    DivX video codec.
    """
    codec_name = 'divx'
    ffmpeg_codec_name = 'mpeg4'

    def __init__(self) -> None:
        super(self.__class__, self).__init__()


class Vp8Codec(VideoCodec):
    """
    Google VP8 video codec.
    """
    codec_name = 'vp8'
    ffmpeg_codec_name = 'libvpx'


class H263Codec(VideoCodec):
    """
    H.263 video codec.
    """
    codec_name = 'h263'
    ffmpeg_codec_name = 'h263'

    def __init__(self) -> None:
        super(self.__class__, self).__init__()


class FlvCodec(VideoCodec):
    """
    Flash Video codec.
    """
    codec_name = 'flv'
    ffmpeg_codec_name = 'flv'

    def __init__(self) -> None:
        super(self.__class__, self).__init__()


class MpegCodec(VideoCodec):
    """
    Base MPEG video codec.
    """
    # Workaround for a bug in ffmpeg in which aspect ratio
    # is not correctly preserved, so we have to set it
    # again in vf; take care to put it *before* crop/pad, so
    # it uses the same adjusted dimensions as the codec itself
    # (pad/crop will adjust it further if neccessary)
    def __init__(self) -> None:
        super(self.__class__, self).__init__()

    def _codec_specific_parse_options(self, safe, stream=0):
        w = safe['width']
        h = safe['height']

        if w and h:
            filters = safe['aspect_filters']
            tmp = 'aspect=%d:%d' % (w, h)

            if filters is None:
                safe['aspect_filters'] = tmp
            else:
                safe['aspect_filters'] = tmp + ',' + filters

        return safe


class Mpeg1Codec(MpegCodec):
    """
    MPEG-1 video codec.
    """
    codec_name = 'mpeg1'
    ffmpeg_codec_name = 'mpeg1video'

    def __init__(self) -> None:
        super(self.__class__, self).__init__()


class Mpeg2Codec(MpegCodec):
    """
    MPEG-2 video codec.
    """
    codec_name = 'mpeg2'
    ffmpeg_codec_name = 'mpeg2video'

    def __init__(self) -> None:
        super(self.__class__, self).__init__()


# Subtitle Codecs
class MOVTextCodec(SubtitleCodec):
    """
    mov_text subtitle codec.
    """
    codec_name = 'mov_text'
    ffmpeg_codec_name = 'mov_text'

    def __init__(self) -> None:
        super(self.__class__, self).__init__()


class SrtCodec(SubtitleCodec):
    """
    SRT subtitle codec.
    """
    codec_name = 'srt'
    ffmpeg_codec_name = 'srt'

    def __init__(self) -> None:
        super(self.__class__, self).__init__()


class WebVTTCodec(SubtitleCodec):
    """
    SRT subtitle codec.
    """
    codec_name = 'webvtt'
    ffmpeg_codec_name = 'webvtt'

    def __init__(self) -> None:
        super(self.__class__, self).__init__()


class SSA(SubtitleCodec):
    """
    SSA (SubStation Alpha) subtitle.
    """
    codec_name = 'ass'
    ffmpeg_codec_name = 'ass'

    def __init__(self) -> None:
        super(self.__class__, self).__init__()


class SubRip(SubtitleCodec):
    """
    SubRip subtitle.
    """
    codec_name = 'subrip'
    ffmpeg_codec_name = 'subrip'

    def __init__(self) -> None:
        super(self.__class__, self).__init__()


class DVBSub(SubtitleCodec):
    """
    DVB subtitles.
    """
    codec_name = 'dvbsub'
    ffmpeg_codec_name = 'dvbsub'

    def __init__(self) -> None:
        super(self.__class__, self).__init__()


class DVDSub(SubtitleCodec):
    """
    DVD subtitles.
    """
    codec_name = 'dvdsub'
    ffmpeg_codec_name = 'dvdsub'

    def __init__(self) -> None:
        super(self.__class__, self).__init__()

video_codec_dict = {}
audio_codec_dict = {}
subtitle_codec_dict = {}

for cls in VideoCodec.__subclasses__():
    video_codec_dict[cls.codec_name] = cls

video_codec_dict['copy'] = VideoCopyCodec
video_codec_dict['x264'] = H264Codec

del video_codec_dict[None]

for cls in AudioCodec.__subclasses__():
    audio_codec_dict[str.lower(cls.codec_name)] = cls

audio_codec_dict['copy'] = AudioCopyCodec

codec_dict = {'video': video_codec_dict,
              'audio': audio_codec_dict,
              'subtitle': subtitle_codec_dict}


for cls in SubtitleCodec.__subclasses__():
    subtitle_codec_dict[str.lower(cls.codec_name)] = cls

subtitle_codec_dict['copy'] = SubtitleCopyCodec

audio_codec_list = [
    AudioNullCodec, AudioCopyCodec, VorbisCodec, AacCodec, Mp3Codec, Mp2Codec,
    FdkAacCodec, FAacCodec, EAc3Codec, Ac3Codec, DtsCodec, FlacCodec
]

video_codec_list = [
    VideoNullCodec, VideoCopyCodec, TheoraCodec, H264Codec, H264QSV, HEVCQSV, H265Codec,
    DivxCodec, Vp8Codec, H263Codec, FlvCodec, Mpeg1Codec, NVEncH264, NVEncH265,
    Mpeg2Codec, H264VAAPI
]

subtitle_codec_list = [
    SubtitleNullCodec, SubtitleCopyCodec, MOVTextCodec, SrtCodec, SSA, SubRip, DVDSub,
    DVBSub, WebVTTCodec
]
