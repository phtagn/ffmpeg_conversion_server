class Parser(object):
    def __init__(self):
        pass

    @staticmethod
    def parse_float(val, default=0.0):
        try:
            return float(val)
        except:
            return default

    @staticmethod
    def parse_int(val, default=0):
        try:
            return int(val)
        except:
            return default


class MediaInfo(object):
    """
    Information about media object, as parsed by ffprobe.
    The attributes are:
      * format - a MediaFormatInfo object
      * streams - a list of MediaStreamInfo objects
    """

    def __init__(self, posters_as_video=True):
        """
        :param posters_as_video: Take poster images (mainly for audio files) as
            A video stream, defaults to True
        """
        self.format = MediaFormatInfo()
        self.posters_as_video = posters_as_video
        self._streams = []
        self._audiostreams = []
        self._videostreams = []
        self._subtitlestreams = []

    @property
    def streams(self):
        return {'video': self._videostreams, 'audio': self._audiostreams, 'subtitle': self._subtitlestreams}

    @property
    def videostreams(self):
        return self._videostreams

    @property
    def audiostreams(self):
        return self._audiostreams

    @property
    def subtitlestreams(self):
        return self._subtitlestreams

    def add_stream(self, streamtype, stream):
        assert isinstance(stream, MediaStreamInfo)
        if stream.type == 'video':
            self._videostreams.append(stream)
        if stream.type == 'audio':
            self._audiostreams.append(stream)
        if stream.type == 'subtitle':
            self._subtitlestreams.append(stream)


class MediaFormatInfo(object):
    """
    Describes the media container format. The attributes are:
      * format - format (short) name (eg. "ogg")
      * fullname - format full (descriptive) name
      * bitrate - total bitrate (bps)
      * duration - media duration in seconds
      * filesize - file size
    """

    def __init__(self):
        self.format = None
        self.fullname = None
        self.bitrate = None
        self.duration = None
        self.filesize = None

    def __repr__(self):
        if self.duration is None:
            return 'MediaFormatInfo(format=%s)' % self.format
        return 'MediaFormatInfo(format=%s, duration=%.2f)' % (self.format,
                                                              self.duration)


class MediaStreamInfo(object):
    """
        Data class to represent media stream data.
        Describes one stream inside a media file. The general
        attributes are:
          * index - stream index inside the container (0-based)
          * type - stream type, either 'audio' or 'video'
          * codec - codec (short) name (e.g "vorbis", "theora")
          * codec_desc - codec full (descriptive) name
          * duration - stream duration in seconds
          * metadata - optional metadata associated with a video or audio stream
          * bitrate - stream bitrate in bytes/second
          * attached_pic - (0, 1 or None) is stream a poster image? (e.g. in mp3)
        """

    def __init__(self,
                 index=None,
                 fmtype=None,
                 codec=None,
                 codec_desc=None,
                 duration=None,
                 bitrate=None,
                 metadata={},
                 disposition={},
                 height=None,
                 width=None,
                 fps=None,
                 level=None,
                 pix_fmt=None,
                 profile=None,
                 bframes=None,
                 channels=None,
                 samplerate=None,
                 forced=None,
                 default=None
                 ):
        self.index = index  # type: int
        self.type = fmtype  # type: str
        self.codec = codec  # type: str
        self.codec_desc = codec_desc  # type: str
        self.duration = duration  # type: int
        self.bitrate = bitrate  # type: int
        self._metadata = metadata  # type: dict
        self._disposition = disposition  # type: dict

        # Video Specific
        self.height = height  # type: int
        self.width = width  # type: int
        self.fps = fps  # type: float
        self.level = level  # type: float
        self.pix_fmt = pix_fmt  # type: str
        self.profile = profile  # type: str
        self.bframes = bframes  # type: int

        # Audio specific
        self.channels = channels  # type: int
        self.samplerate = samplerate  # type: float

        # Subtitle specific
        self.forced = forced  # type: int
        self.default = default  # type: int

    @property
    def metadata(self):
        return self._metadata

    @metadata.setter
    def metadata(self, value):
        self._metadata.update(value)

    @property
    def disposition(self):
        return self._disposition

    @disposition.setter
    def disposition(self, value):
        self._disposition.update(value)

    def should_transcode(self, target):
        """Returns true if you need transcoding to go from this to the target.
        If an attribute is None in the target or in self it is disregarded in the test"""
        assert isinstance(target, MediaStreamInfo)

        if self.type != target.type:
            raise Exception('Target type does not match. Cannot compare accross types.')

        if self.codec != target.codec:
            return True

        elif self.height and target.height and self.height > target.height:
            return True

        elif self.width and target.width and self.width > target.width:
            return True

        elif self.bitrate and target.bitrate and self.bitrate > target.bitrate:
            return True

        elif self.level and target.level and self.level > target.level:
            return True

        elif self.pix_fmt and target.pix_fmt and self.pix_fmt != target.pix_fmt:
            return True

        elif self.profile and target.profile and self.profile != target.profile:
            return True

        elif self.bframes and target.bframes and self.bframes > target.bframes:
            return True

        elif self.channels and target.channels and self.channels > target.channels:
            return True

        elif self.samplerate and target.samplerate and self.samplerate > target.samplerate:
            return True

        else:
            return False
