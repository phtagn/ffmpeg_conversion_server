import os
from io import BytesIO
from mutagen.mp4 import MP4, MP4Cover
import abc
import logging

log = logging.getLogger(__name__)

class TagError(Exception):
    pass

class ITagger(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def write(self):
        pass

class TaggerFactory(object):
    Taggers = {}

    @classmethod
    def register(cls, tagger):
        cls.Taggers.update({tagger.name: tagger})

    @classmethod
    def get(cls, tagger: str, tags, filepath: str, artworkfile=None):
        if tagger in TaggerFactory.Taggers:
            return cls.Taggers[tagger](tags, filepath, artworkfile=artworkfile)
        else:
            return None


class MP4Tagger(ITagger):
    supported_containers = ['mp4']
    name = 'mp4'

    tagtable = {
                'description': 'desc',
                'long_description': 'ldes',
                'genre': '\xa9gen',
                'title': '\xa9nam',
                'show': 'tvsh',
                'episode_title': 'tven',
                'network': 'tvnn',
                'season_number': 'tvsn',
                'season_total': 'disk',
                'episode_number': 'tves',
                'track_number': 'trkn',
                'album': '\xa9alb',
                'itunes_video_category': 'stik',
                'resolution': 'hdvd'}


    def __init__(self, tags, mp4Path, dimensions={}, artworkfile=None):
        self.mp4Path = mp4Path
        self.tags = tags
        self.artworkfile = artworkfile
        self.dimensions = dimensions

        if os.path.isfile(mp4Path):
            self.video = MP4(self.mp4Path)
        else:
            log.error('Path %s is not valid', mp4Path)

        ext = os.path.splitext(self.mp4Path)[1][1:]
        if ext.lower() not in ['mp4', 'm4v', 'mov']:
            raise TaggerException('MP4Tagger only tags mp4, the file extention is %s', ext)

    def writetags(self):

        self.settag('description', self.tags.description)
        self.settag('long_description', self.tags.long_description)
        self.settag('genre', self.tags.genre)
        self.settag('title', self.tags.title)
        self.settag('date', self.tags.date)
        self.settag('show', self.tags.show)
        self.settag('episode_title', self.tags.title)
        self.settag('network', self.tags.network)
        self.settag('season_total', [(self.tags.season_total, 0)])
        self.settag('album', f'{self.tags.show}, Season {self.tags.season_total}')
        self.settag('episode_number', [self.tags.episode_number])
        self.settag('track_number', [(self.tags.episode_number, self.tags.season_total)])
        self.settag('resolution', self.dimensions)

        if self.tags.season_number:
            self.settag('itunes_video_category', [10])
        else:
            self.settag('itunes_video_category', [9])

        self.video["----:com.apple.iTunes:iTunMOVI"] = self.xmlTags()  # XML - see xmlTags method
        # self.video["----:com.apple.iTunes:iTunEXTC"] = self.setRating()  # iTunes content rating

        if self.artworkfile:
            cover = open(self.artworkfile, 'rb').read()
            if self.artworkfile.endswith('png'):
                self.video["covr"] = [MP4Cover(cover, MP4Cover.FORMAT_PNG)]  # png poster
            else:
                self.video["covr"] = [MP4Cover(cover, MP4Cover.FORMAT_JPEG)]  # jpeg poster

        MP4(self.mp4Path).delete(self.mp4Path)
        self.video.save()


    def settag(self, tag, tagdata=None) -> None:

        if tag in MP4Tagger.tagtable and tagdata:
            mp4tag = MP4Tagger.tagtable[tag]
            self.video[mp4tag] = tagdata
        else:
            log.debug('Tag %s was not written because data %s was missing', tag, tagdata)

    @staticmethod
    def setHD(dimensions):
        HD = [0]

        if dimensions['width'] >= 1900 or dimensions['height'] >= 1060:
            HD = [2]
        elif dimensions['width'] >= 1260 or dimensions['height'] >= 700:
            HD = [1]

        return HD

    def xmlTags(self):
        # constants
        header = b"<?xml version=\"1.0\" encoding=\"UTF-8\"?><!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\"><plist version=\"1.0\"><dict>\n"
        castheader = b"<key>cast</key><array>\n"
        writerheader = b"<key>screenwriters</key><array>\n"
        directorheader = b"<key>directors</key><array>\n"
        subfooter = b"</array>\n"
        footer = b"</dict></plist>\n"

        output = BytesIO()
        output.write(header)

        # Write actors
        if self.tags.cast:
            output.write(castheader)
            for name in self.tags.cast:
                tag = name if name.__class__ is bytes else name.encode('ascii', errors='ignore')
                output.write(b"<dict><key>name</key><string>%s</string></dict>\n" % tag)
                output.write(subfooter)

        # Write screenwriterr
        if self.tags.writers:
            output.write(writerheader)
            for name in self.tags.writers:
                tag = name if name.__class__ is bytes else name.encode('ascii', errors='ignore')
                output.write(
                    b"<dict><key>name</key><string>%s</string></dict>\n" % tag)
            output.write(subfooter)


        # Write directors
        if self.tags.directors:
            output.write(directorheader)
            for name in self.tags.directors:
                tag = name if name.__class__ is bytes else name.encode('ascii', errors='ignore')
                output.write(
                    b"<dict><key>name</key><string>%s</string></dict>\n" % tag)
            output.write(subfooter)

        # Close XML

        output.write(footer)
        return output.getvalue()

TaggerFactory.register(MP4Tagger)

class TaggerException(Exception):
    pass



