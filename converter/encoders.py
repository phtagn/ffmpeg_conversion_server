#!/usr/bin/env python
from typing import Dict, Union


class BaseEncoder(object):
    """
    Base audio/video codec class.
    """
    defaults = {}
    encoder_options = {}
    codec_name = None
    ffmpeg_codec_name = None

    def __init__(self, opts):
        self.safeopts = {}
        self.add_options(opts)

    def parse_options(self, stream=0):
        return None

    def _codec_specific_parse_options(self, safe: Dict[str, Union[str, int]]):
        return safe

    def _codec_specific_produce_ffmpeg_list(self, safe: Dict[str, Union[str, int]], stream: int = 0):
        return []

    def add_options(self, opts: Dict[str, Union[str, int]]) -> None:

        # Only copy options that are expected and of correct type
        # (and do typecasting on them)
        for k, v in opts.items():
            if k in self.encoder_options:
                if v is not None and v is not '':  # Don't accept empty strings or None
                    typ = self.encoder_options[k]
                    try:
                        self.safeopts[k] = typ(v)
                    except:
                        pass


class AudioEncoder(BaseEncoder):
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

    defaults = {
    }

    def parse_options(self, stream=0):
        # super(AudioEncoder, self).parse_options(opt)
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

        optlist.extend(self._codec_specific_produce_ffmpeg_list(safe, stream))
        return optlist


class SubtitleEncoder(BaseEncoder):
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

    defaults = {}

    def parse_options(self, stream=0):
        # super(SubtitleEncoder, self).parse_options(opt)
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

        optlist.extend(self._codec_specific_produce_ffmpeg_list(safe, stream))
        return optlist


class VideoEncoder(BaseEncoder):
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

    defaults = {}

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

    def parse_options(self, stream=0):
        super(VideoEncoder, self).parse_options()
        stream = str(stream)
        safe = self.safeopts

        if 'fps' in self.safeopts:
            f = self.safeopts['fps']
            if f < 1 or f > 120:
                del self.safeopts['fps']

        if 'bitrate' in self.safeopts:
            br = self.safeopts['bitrate']
            if br < 16 or br > 15000:
                del self.safeopts['bitrate']

        if 'crf' in self.safeopts:
            crf = self.safeopts['crf']
            if crf < 0 or crf > 51:
                del self.safeopts['crf']

        w = None
        h = None

        if 'width' in self.safeopts:
            w = self.safeopts['width']
            if w < 16 or w > 4000:
                w = None

        if 'height' in self.safeopts:
            h = self.safeopts['height']
            if h < 16 or h > 3000:
                h = None

        sw = None
        sh = None

        if 'src_width' in self.safeopts and 'src_height' in self.safeopts:
            sw = self.safeopts['src_width']
            sh = self.safeopts['src_height']
            if not sw or not sh:
                sw = None
                sh = None

        mode = 'stretch'
        if 'mode' in self.safeopts:
            if self.safeopts['mode'] in ['stretch', 'crop', 'pad']:
                mode = self.safeopts['mode']

        ow, oh = w, h  # FIXED
        w, h, filters = self._aspect_corrections(sw, sh, w, h, mode)

        if w:
            self.safeopts['width'] = w
        if h:
            self.safeopts['height'] = h
        if filters:
            self.safeopts['aspect_filters'] = filters

        if w and h:
            self.safeopts['aspect'] = '%d:%d' % (w, h)

        self._codec_specific_parse_options(self.safeopts)

        if 'width' in self.safeopts:
            w = self.safeopts['width']
        if 'height' in self.safeopts:
            h = self.safeopts['height']
        if 'filters' in self.safeopts:
            filters = self.safeopts['aspect_filters']

        optlist = ['-vcodec', self.ffmpeg_codec_name]
        if 'map' in self.safeopts:
            optlist.extend(['-map', '0:' + str(self.safeopts['map'])])
        if 'fps' in self.safeopts:
            optlist.extend(['-r', str(self.safeopts['fps'])])
        if 'pix_fmt' in self.safeopts:
            optlist.extend(['-pix_fmt', str(self.safeopts['pix_fmt'])])
        if 'bitrate' in self.safeopts:
            optlist.extend(['-vb', str(br) + 'k'])  # FIXED
        if 'crf' in self.safeopts:
            optlist.extend(['-crf', str(self.safeopts['crf'])])
        if 'filter' in self.safeopts:
            if filters:
                filters = '%s;%s' % (filters, str(self.safeopts['filter']))
            else:
                filters = str(self.safeopts['filter'])
        if w and h:
            optlist.extend(['-s', '%dx%d' % (w, h)])

            if ow and oh:
                optlist.extend(['-aspect', '%d:%d' % (ow, oh)])

        if filters:
            optlist.extend(['-vf', filters])

        optlist.extend(self._codec_specific_produce_ffmpeg_list(self.safeopts))

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


class AudioNullEncoder(BaseEncoder):
    """
    Null audio codec (no audio).
    """
    codec_name = None
    codec_type = 'audio'

    def parse_options(self, stream=0):
        return ['-an']


class VideoNullEncoder(BaseEncoder):
    """
    Null video codec (no video).
    """

    codec_name = None
    codec_type = 'video'

    def parse_options(self):
        return ['-vn']


class SubtitleNullEncoder(BaseEncoder):
    """
    Null subtitle codec (no subtitle)
    """

    codec_name = None
    codec_type = 'subtitle'

    def parse_options(self, stream=0):
        return ['-sn']


class AudioCopyEncoder(BaseEncoder):
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

    def __init__(self, opts) -> None:
        super(AudioCopyEncoder, self).__init__(opts)

    def parse_options(self, stream=0):
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


class VideoCopyEncoder(BaseEncoder):
    """
    Copy video stream directly from the source.
    """

    def __init__(self, opts) -> None:
        super(VideoCopyEncoder, self).__init__(opts)

    codec_name = 'copy'
    codec_type = 'video'
    encoder_options = {'map': int,
                       'source': str}

    def parse_options(self, stream=0):
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


class SubtitleCopyEncoder(BaseEncoder):
    """
    Copy subtitle stream directly from the source.
    """
    codec_name = 'copy'
    codec_type = 'subtitle'
    encoder_options = {'map': int,
                       'source': str}

    def __init__(self, opts) -> None:
        super(SubtitleCopyEncoder, self).__init__(opts)

    def parse_options(self, stream=0):
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
class VorbisCodec(AudioEncoder):
    """
    Vorbis audio codec.
    """

    def __init__(self, opts) -> None:
        super(VorbisCodec, self).__init__(opts)

    codec_name = 'vorbis'
    ffmpeg_codec_name = 'libvorbis'
    encoder_options = AudioEncoder.encoder_options.copy()
    encoder_options.update({
        'quality': int,  # audio quality. Range is 0-10(highest quality)
        # 3-6 is a good range to try. Default is 3
    })
    defaults = AudioEncoder.defaults.copy()
    defaults.update({'quality': 'integer(default=3)'})

    def _codec_specific_produce_ffmpeg_list(self, safe, stream=0):
        optlist = []
        stream = str(stream)
        if 'quality' in safe:
            optlist.extend(['-qscale:a:' + stream, str(safe['quality'])])
        return optlist


class AacCodec(AudioEncoder):
    """
    AAC audio codec.
    """
    codec_name = 'aac'
    ffmpeg_codec_name = 'aac'

    def __init__(self, opts) -> None:
        super(AacCodec, self).__init__(opts)

    def parse_options(self, stream=0):
        if 'channels' in self.safeopts:
            c = self.safeopts['channels']
            if c > 6:
                self.safeopts['channels'] = 6
        return super(AacCodec, self).parse_options(stream)


class FdkAacCodec(AudioEncoder):
    """
    AAC audio codec.
    """
    codec_name = 'libfdk_aac'
    ffmpeg_codec_name = 'libfdk_aac'

    def __init__(self, opts) -> None:
        super(FdkAacCodec, self).__init__(opts)

    def parse_options(self, stream=0):
        if 'channels' in self.safeopts:
            c = self.safeopts['channels']
            if c > 6:
                self.safeopts['channels'] = 6
        return super(FdkAacCodec, self).parse_options(stream)


class FAacCodec(AudioEncoder):
    """
    AAC audio codec.
    """
    codec_name = 'libfaac'
    ffmpeg_codec_name = 'libfaac'

    def __init__(self, opts) -> None:
        super(FAacCodec, self).__init__(opts)

    def parse_options(self, stream=0):
        if 'channels' in self.safeopts:
            c = self.safeopts['channels']
            if c > 6:
                self.safeopts['channels'] = 6
        return super(FAacCodec, self).parse_options(stream)


class Ac3Codec(AudioEncoder):
    """
    AC3 audio codec.
    """
    codec_name = 'ac3'
    ffmpeg_codec_name = 'ac3'

    def __init__(self, opts) -> None:
        super(Ac3Codec, self).__init__(opts)

    def parse_options(self, stream=0):
        if 'channels' in self.safeopts:
            c = self.safeopts['channels']
            if c > 6:
                self.safeopts['channels'] = 6
        return super(Ac3Codec, self).parse_options(stream)


class EAc3Codec(AudioEncoder):
    """
    Dolby Digital Plus/EAC3 audio codec.
    """
    codec_name = 'eac3'
    ffmpeg_codec_name = 'eac3'

    def __init__(self, opts) -> None:
        super(EAc3Codec, self).__init__(opts)

    def parse_options(self, stream=0):
        if 'channels' in self.safeopts:
            c = self.safeopts['channels']
            if c > 8:
                self.safeopts['channels'] = 8
        if 'bitrate' in self.safeopts:
            br = self.safeopts['bitrate']
            if br > 640:
                self.safeopts['bitrate'] = 640
        return super(EAc3Codec, self).parse_options(stream)


class FlacCodec(AudioEncoder):
    """
    FLAC audio codec.
    """
    codec_name = 'flac'
    ffmpeg_codec_name = 'flac'

    # flac_experimental_enable = ['-strict', 'experimental']

    def __init__(self, opts) -> None:
        super(FlacCodec, self).__init__(opts)

    # def _codec_specific_produce_ffmpeg_list(self, safe, stream=0):
    # return self.flac_experimental_enable


class DtsCodec(AudioEncoder):
    """
    DTS audio codec.
    """
    codec_name = 'dts'
    ffmpeg_codec_name = 'dca'
    dca_experimental_enable = ['-strict', '-2']

    def __init__(self, opts) -> None:
        super(DtsCodec, self).__init__(opts)

    def parse_options(self, stream=0):
        if 'bitrate' in self.safeopts:
            if self.safeopts['bitrate'] < 271:
                self.safeopts['bitrate'] = 271

        return super(DtsCodec, self).parse_options(stream)

    def _codec_specific_produce_ffmpeg_list(self, safe, stream=0):

        return self.dca_experimental_enable


class Mp3Codec(AudioEncoder):
    """
    MP3 (MPEG layer 3) audio codec.
    """
    codec_name = 'mp3'
    ffmpeg_codec_name = 'libmp3lame'

    def __init__(self, opts) -> None:
        super(Mp3Codec, self).__init__(opts)


class Mp2Codec(AudioEncoder):
    """
    MP2 (MPEG layer 2) audio codec.
    """
    codec_name = 'mp2'
    ffmpeg_codec_name = 'mp2'

    def __init__(self, opts) -> None:
        super(Mp2Codec, self).__init__(opts)


# Video Codecs
class TheoraCodec(VideoEncoder):
    """
    Theora video codec.
    """
    codec_name = 'theora'
    ffmpeg_codec_name = 'libtheora'
    encoder_options = VideoEncoder.encoder_options.copy()
    encoder_options.update({
        'quality': int,  # audio quality. Range is 0-10(highest quality)
        # 5-7 is a good range to try (default is 200k bitrate)
    })
    defaults = VideoCopyEncoder.defaults.copy()
    defaults.update({'quality': 'integer(default=5)'})

    def __init__(self, opts) -> None:
        super(TheoraCodec, self).__init__(opts)

    def _codec_specific_produce_ffmpeg_list(self, safe, stream=0):
        optlist = []
        if 'quality' in safe:
            optlist.extend(['-qscale:v', safe['quality']])
        return optlist


class H264Codec(VideoEncoder):
    """
    H.264/AVC video codec.
    """
    codec_name = 'h264'
    ffmpeg_codec_name = 'libx264'
    encoder_options = VideoEncoder.encoder_options.copy()
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

    defaults = VideoEncoder.defaults.copy()
    defaults.update({'preset': 'string(default=None)',
                     'crf': 'integer(default=23)',
                     'tune': 'string(default=None)'
                     })

    def __init__(self, opts) -> None:
        super(H264Codec, self).__init__(opts)

    def parse_options(self, stream=0):

        if 'width' in self.safeopts:
            self.safeopts['wscale'] = self.safeopts['width']
            del (self.safeopts['width'])
        if 'height' in self.safeopts:
            self.safeopts['hscale'] = self.safeopts['height']
            del (self.safeopts['height'])
        if 'crf' in self.safeopts and 'bitrate' in self.safeopts:
            del (self.safeopts['bitrate'])

        return super(H264Codec, self).parse_options(stream)

    def _codec_specific_produce_ffmpeg_list(self, safe, stream=0):
        optlist = []
        if 'level' in self.safeopts:
            if self.safeopts['level'] < 3.0 or self.safeopts['level'] > 4.2:
                del self.safeopts['level']

        if 'wscale' in safe and not safe['wscale']:
            del safe['wscale']
        if 'hscale' in safe and not safe['hscale']:
            del safe['hscale']

        if 'preset' in self.safeopts:
            optlist.extend(['-preset', self.safeopts['preset']])
        if 'quality' in self.safeopts:
            optlist.extend(['-crf', str(self.safeopts['quality'])])
        if 'profile' in self.safeopts:
            optlist.extend(['-profile:v', self.safeopts['profile']])
        if 'level' in self.safeopts:
            optlist.extend(['-level', '%0.1f' % self.safeopts['level']])
        if 'tune' in self.safeopts:
            optlist.extend(['-tune', self.safeopts['tune']])
        if 'wscale' in self.safeopts and 'hscale' in self.safeopts:
            optlist.extend(['-vf', 'scale=%s:%s' % (self.safeopts['wscale'], self.safeopts['hscale'])])
        elif 'wscale' in self.safeopts:
            optlist.extend(['-vf', 'scale=%s:trunc(ow/a/2)*2' % (self.safeopts['wscale'])])
        elif 'hscale' in self.safeopts:
            optlist.extend(['-vf', 'scale=trunc((oh*a)/2)*2:%s' % (self.safeopts['hscale'])])
        return optlist


class X264(H264Codec):
    """
    Alias for H264
    """
    codec_name = 'x264'

    def __init__(self, opts) -> None:
        super(X264, self).__init__(opts)


class NVEncH264(H264Codec):
    """
    Nvidia H.264/AVC video codec.
    """
    codec_name = 'nvenc_h264'
    ffmpeg_codec_name = 'nvenc_h264'

    def __init__(self, opts) -> None:
        super(NVEncH264, self).__init__(opts)


class H264VAAPI(H264Codec):
    """
    H.264/AVC video codec.
    """
    codec_name = 'h264vaapi'
    ffmpeg_codec_name = 'h264_vaapi'
    encoder_options = H264Codec.encoder_options.copy()
    encoder_options.update({'vaapi_device': str})

    defaults = H264Codec.defaults.copy()
    defaults.update({'vaapi_device': 'string(default=/dev/dri/renderD128)'})

    def __init__(self, opts) -> None:
        super(H264VAAPI, self).__init__(opts)

    def _codec_specific_produce_ffmpeg_list(self, safe: dict, stream=0):
        optlist = []
        optlist.extend(['-vaapi_device', '/dev/dri/renderD128'])
        if 'vaapi_device' in safe:
            optlist.extend(['-vaapi_device', safe['vaapi_device']])
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

    def __init__(self, opts) -> None:
        super(H264QSV, self).__init__(opts)

    def _codec_specific_produce_ffmpeg_list(self, safe, stream=0):
        optlist = []
        optlist.extend(['-look_ahead', '0'])
        return optlist


class H265Codec(VideoEncoder):
    """
    H.265/AVC video codec.
    """
    codec_name = 'h265'
    ffmpeg_codec_name = 'libx265'
    encoder_options = VideoEncoder.encoder_options.copy()
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

    defaults = VideoEncoder.defaults.copy()
    defaults.update({'preset': 'string(default=None)',
                     'crf': 'integer(default=23)',
                     'tune': 'string(default=None)'
                     })

    def __init__(self, opts) -> None:
        super(H265Codec, self).__init__(opts)

    def parse_options(self, stream=0):
        if 'width' in self.safeopts:
            self.safeopts['wscale'] = self.safeopts['width']
            del (self.safeopts['width'])
        if 'height' in self.safeopts:
            self.safeopts['hscale'] = self.safeopts['height']
            del (self.safeopts['height'])
        if 'crf' in self.safeopts and 'bitrate' in self.safeopts:
            del (self.safeopts['bitrate'])
        return super(H265Codec, self).parse_options(stream)

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
        if 'wscale' in safe and 'hscale' in safe and safe['wscale'] and safe['hscale']:
            optlist.extend(['-vf', 'scale=%s:%s' % (safe['wscale'], safe['hscale'])])
        elif 'wscale' in safe and safe['wscale']:
            optlist.extend(['-vf', 'scale=%s:trunc(ow/a/2)*2' % (safe['wscale'])])
        elif 'hscale' in safe and safe['hscale']:
            optlist.extend(['-vf', 'scale=trunc((oh*a)/2)*2:%s' % (safe['hscale'])])
        optlist.extend(['-tag:v', 'hvc1'])
        return optlist


class HEVCQSV(H265Codec):
    """
    HEVC video codec.
    """
    codec_name = 'hevcqsv'
    ffmpeg_codec_name = 'hevc_qsv'

    def __init__(self, opts) -> None:
        super(HEVCQSV, self).__init__(opts)


class NVEncH265(H265Codec):
    """
    Nvidia H.265/AVC video codec.
    """
    codec_name = 'nvenc_h265'
    ffmpeg_codec_name = 'hevc_nvenc'

    def __init__(self, opts) -> None:
        super(NVEncH265, self).__init__(opts)


class DivxCodec(VideoEncoder):
    """
    DivX video codec.
    """
    codec_name = 'divx'
    ffmpeg_codec_name = 'mpeg4'

    def __init__(self, opts) -> None:
        super(DivxCodec, self).__init__(opts)


class Vp8Codec(VideoEncoder):
    """
    Google VP8 video codec.
    """
    codec_name = 'vp8'
    ffmpeg_codec_name = 'libvpx'

    def __init__(self, opts) -> None:
        super(Vp8Codec, self).__init__(opts)


class H263Codec(VideoEncoder):
    """
    H.263 video codec.
    """
    codec_name = 'h263'
    ffmpeg_codec_name = 'h263'

    def __init__(self, opts) -> None:
        super(H263Codec, self).__init__(opts)


class FlvCodec(VideoEncoder):
    """
    Flash Video codec.
    """
    codec_name = 'flv'
    ffmpeg_codec_name = 'flv'

    def __init__(self, opts) -> None:
        super(FlvCodec, self).__init__(opts)


class MpegCodec(VideoEncoder):
    """
    Base MPEG video codec.
    """

    # Workaround for a bug in ffmpeg in which aspect ratio
    # is not correctly preserved, so we have to set it
    # again in vf; take care to put it *before* crop/pad, so
    # it uses the same adjusted dimensions as the codec itself
    # (pad/crop will adjust it further if neccessary)
    def __init__(self, opts) -> None:
        super(MpegCodec, self).__init__(opts)

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

    def __init__(self, opts) -> None:
        super(Mpeg1Codec, self).__init__(opts)


class Mpeg2Codec(MpegCodec):
    """
    MPEG-2 video codec.
    """
    codec_name = 'mpeg2'
    ffmpeg_codec_name = 'mpeg2video'

    def __init__(self, opts) -> None:
        super(Mpeg2Codec, self).__init__(opts)


# Subtitle Codecs
class MOVTextCodec(SubtitleEncoder):
    """
    mov_text subtitle codec.
    """
    codec_name = 'mov_text'
    ffmpeg_codec_name = 'mov_text'

    def __init__(self, opts) -> None:
        super(MOVTextCodec, self).__init__(opts)


class SrtCodec(SubtitleEncoder):
    """
    SRT subtitle codec.
    """
    codec_name = 'srt'
    ffmpeg_codec_name = 'srt'

    def __init__(self, opts) -> None:
        super(SrtCodec, self).__init__(opts)


class WebVTTCodec(SubtitleEncoder):
    """
    SRT subtitle codec.
    """
    codec_name = 'webvtt'
    ffmpeg_codec_name = 'webvtt'

    def __init__(self, opts) -> None:
        super(WebVTTCodec, self).__init__(opts)


class SSA(SubtitleEncoder):
    """
    SSA (SubStation Alpha) subtitle.
    """
    codec_name = 'ass'
    ffmpeg_codec_name = 'ass'

    def __init__(self, opts) -> None:
        super(SSA, self).__init__(opts)


class SubRip(SubtitleEncoder):
    """
    SubRip subtitle.
    """
    codec_name = 'subrip'
    ffmpeg_codec_name = 'subrip'

    def __init__(self, opts) -> None:
        super(SubRip, self).__init__(opts)


class DVBSub(SubtitleEncoder):
    """
    DVB subtitles.
    """
    codec_name = 'dvbsub'
    ffmpeg_codec_name = 'dvbsub'

    def __init__(self, opts) -> None:
        super(DVBSub, self).__init__(opts)


class DVDSub(SubtitleEncoder):
    """
    DVD subtitles.
    """
    codec_name = 'dvdsub'
    ffmpeg_codec_name = 'dvdsub'

    def __init__(self, opts) -> None:
        super(DVDSub, self).__init__(opts)


class EncoderFactory(object):
    codecs = {'video': {}, 'audio': {}, 'subtitle': {}}

    @classmethod
    def register(cls, codec):
        cls.codecs[codec.codec_type].update({codec.codec_name: codec})

    @classmethod
    def get(cls, codec: str, typ: str, cfg):
        return cls.codecs[typ][codec](cfg[typ][codec])

    @classmethod
    def getvideo(cls, codec: str, cfg):
        if codec == 'copy':
            return cls.codecs['video']['copy'](cfg)
        elif codec == 'null':
            return cls.codecs['video']['null']()
        else:
            return cls.codecs['video'][codec](cfg['video'][codec])

    @classmethod
    def getaudio(cls, codec: str, cfg):
        return cls.codecs['audio'][codec](cfg['audio'][codec])

    @classmethod
    def getsubtitle(cls, codec: str, cfg):
        return cls.codecs['subtitle'][codec](cfg['subtitle'][codec])


# Video Codecs
EncoderFactory.register(VideoCopyEncoder)
EncoderFactory.register(TheoraCodec)
EncoderFactory.register(H264Codec)
EncoderFactory.register(H264QSV)
EncoderFactory.register(HEVCQSV)
EncoderFactory.register(H265Codec)
EncoderFactory.register(DivxCodec)
EncoderFactory.register(Vp8Codec)
EncoderFactory.register(H263Codec)
EncoderFactory.register(FlvCodec)
EncoderFactory.register(Mpeg1Codec)
EncoderFactory.register(Mpeg2Codec)
EncoderFactory.register(NVEncH264)
EncoderFactory.register(NVEncH265)
EncoderFactory.register(H264VAAPI)

# Audio Codecs
EncoderFactory.register(AudioCopyEncoder)
EncoderFactory.register(VorbisCodec)
EncoderFactory.register(AacCodec)
EncoderFactory.register(Mp3Codec)
EncoderFactory.register(Mp2Codec)
EncoderFactory.register(FdkAacCodec)
EncoderFactory.register(FAacCodec)
EncoderFactory.register(EAc3Codec)
EncoderFactory.register(Ac3Codec)
EncoderFactory.register(DtsCodec)
EncoderFactory.register(FlacCodec)

# Subtitle Codecs
EncoderFactory.register(SubtitleCopyEncoder)
EncoderFactory.register(MOVTextCodec)
EncoderFactory.register(SrtCodec)
EncoderFactory.register(SSA)
EncoderFactory.register(SubRip)
EncoderFactory.register(DVDSub)
EncoderFactory.register(DVBSub)
EncoderFactory.register(WebVTTCodec)

audio_codec_list = [
    AudioNullEncoder, AudioCopyEncoder, VorbisCodec, AacCodec, Mp3Codec, Mp2Codec,
    FdkAacCodec, FAacCodec, EAc3Codec, Ac3Codec, DtsCodec, FlacCodec
]

video_codec_list = [
    VideoNullEncoder, VideoCopyEncoder, TheoraCodec, H264Codec, H264QSV, HEVCQSV, H265Codec,
    DivxCodec, Vp8Codec, H263Codec, FlvCodec, Mpeg1Codec, NVEncH264, NVEncH265,
    Mpeg2Codec, H264VAAPI
]

subtitle_codec_list = [
    SubtitleNullEncoder, SubtitleCopyEncoder, MOVTextCodec, SrtCodec, SSA, SubRip, DVDSub,
    DVBSub, WebVTTCodec
]
