import os
from io import StringIO

from extensions import valid_output_extensions
from mutagen.mp4 import MP4, MP4Cover


class TagError(Exception):
    pass


class Tagger(object):
    def __init__(self, info, mp4Path):
        """
        :type mp4Path: str
        :type info : fetchers.Info
        """
        self.mp4Path = mp4Path
        assert isinstance(info, fetchers.Info)
        self.info = info

    def writetag(self):

        ext = os.path.splitext(self.mp4Path)[1][1:]
        if ext not in valid_output_extensions:
            raise TaggerException

        video = MP4(self.mp4Path)

        video["desc"] = self.info.description
        video["ldes"] = self.info.ldescription
        video["\xa9gen"] = self.info.genre

        video["\xa9nam"] = self.info.title  # Video title

        if self.info.date != "0000-00-00":
            video["\xa9day"] = self.info.date  # Airdate

        if isinstance(self.info, fetchers.TvInfo):
            video["tvsh"] = self.info.show  # TV show title
            video["tven"] = self.info.title  # Episode title
            video["tvnn"] = self.info.network  # Network
            video["tvsn"] = [self.info.season]  # Season number
            video["disk"] = [(self.info.season, 0)]  # Season number as disk
            video["\xa9alb"] = f'{self.info.show}, Season {self.info.seasons}'  # iTunes Album as Season
            video["tves"] = [self.info.episode]  # Episode number
            video["trkn"] = [(self.info.episode, self.info.seasons)]  # Episode number iTunes
            video["stik"] = [10]  # TV show iTunes category

        elif isinstance(self.info, fetchers.MovieInfo):
            video["stik"] = [9]

        # if self.HD is not None:
        #    video["hdvd"] = self.HD

        video["----:com.apple.iTunes:iTunMOVI"] = self.xmlTags()  # XML - see xmlTags method
        # video["----:com.apple.iTunes:iTunEXTC"] = self.setRating()  # iTunes content rating

        if self.info.artworkpath:
            cover = open(self.info.artworkpath, 'rb').read()
            if self.info.artworkpath.endswith('png'):
                video["covr"] = [MP4Cover(cover, MP4Cover.FORMAT_PNG)]  # png poster
            else:
                video["covr"] = [MP4Cover(cover, MP4Cover.FORMAT_JPEG)]  # jpeg poster

        MP4(self.mp4Path).delete(self.mp4Path)
        video.save()

    def rating(self):
        pass

    def setHD(self):
        if width >= 1900 or height >= 1060:
            self.HD = [2]
        elif width >= 1260 or height >= 700:
            self.HD = [1]
        else:
            self.HD = [0]

    def xmlTags(self):
        # constants
        header = "<?xml version=\"1.0\" encoding=\"UTF-8\"?><!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\"><plist version=\"1.0\"><dict>\n"
        castheader = "<key>cast</key><array>\n"
        writerheader = "<key>screenwriters</key><array>\n"
        directorheader = "<key>directors</key><array>\n"
        subfooter = "</array>\n"
        footer = "</dict></plist>\n"

        output = StringIO()
        output.write(header)

        # Write actors
        if self.info.cast:
            output.write(castheader)
            for name in self.info.cast:
                output.write("<dict><key>name</key><string>%s</string></dict>\n" % name.encode('ascii',
                                                                                               errors='ignore'))
                output.write(subfooter)

        # Write screenwriterr
        if self.info.writers:
            output.write(writerheader)
            for name in self.info.writers:
                output.write(
                    "<dict><key>name</key><string>%s</string></dict>\n" % name.encode('ascii', errors='ignore'))
            output.write(subfooter)

        # Write directors
        if self.info.director:
            output.write(directorheader)
            for name in self.info.director:
                output.write(
                    "<dict><key>name</key><string>%s</string></dict>\n" % name.encode('ascii', errors='ignore'))
            output.write(subfooter)

        # Close XML
        output.write(footer)
        return output.getvalue()


class TaggerException(Exception):
    pass


if __name__ == '__main__':
    import fetchers

    Fetchers = fetchers.FetchersFactory()
    Fetchers.InitFetchers('fr')

    fetcher = Fetchers.GetFetcherBySource('tvdb', 'tv')

    showinfo = {
        'showid': 176941,
        'season': 2,
        'episode': 2
    }

    myinfo = fetcher.fetch(showinfo)
    myinfo.artworkpath = fetcher.getArtwork(showinfo)

    testfile = ''

    mytagger = Tagger(myinfo, testfile)
    mytagger.writetag()
