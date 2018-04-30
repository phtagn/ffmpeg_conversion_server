import logging
import os
import sys
from logging.config import fileConfig

import containers
import fetchers
import settings
from converter import Converter
from extensions import valid_input_extensions, valid_output_extensions

fileConfig(os.path.join(os.path.dirname(sys.argv[0]), 'logging.ini'),
           defaults={'logfilename': os.path.join(os.path.dirname(sys.argv[0]), 'server.log')})


def parse_file(path):
    path = os.path.abspath(path)
    input_dir, filename = os.path.split(path)
    filename, input_extension = os.path.splitext(filename)
    input_extension = input_extension[1:]
    return input_dir, filename, input_extension


class BaseJob(object):
    converter = None

    def __init__(self, request):
        self.log = logging.getLogger(__name__)
        try:
            if os.path.isfile(request['inputfile']):
                self.fullpath = request['inputfile']
                self.inputdir, self.inputfile, self.inputext = parse_file(self.fullpath)
            else:
                raise JobException(f"{request['inputfile']} cannot be found")

            self.requester = request['requester']
            self.original = request['original'] if request['original'] else None
            self.id = request['id']
            self.id_type = request['id_type']



        except KeyError:
            raise Exception('Request dict should contain keys: requester, inputfile, original, id, id_type, settings')

        try:
            self.settings = settings.SettingsManager.getsettings(request['settings'])
        except:
            raise Exception(
                f'Could not load settings {request["settings"]}. Available setttings are {settings.SettingsManager.settings.keys()}')



        if not self.__class__.converter:
            self.__class__.converter = Converter(self.settings.FFMPEG.ffmpeg, self.settings.FFMPEG.ffprobe)

        self.fileinfo = self.__class__.converter.probe(self.fullpath)

        self.container = containers.MP4(self.settings.MP4, self.fileinfo, logger=self.log)  # TODO : remove test value
        self.outputfile = os.path.join(self.inputdir, f'{self.inputfile}.{self.container.extensions[0]}')
        # self.getdimensions()

        # self.tags = self.fetchtags().fetch(self)

        self.preopts = []
        self.postopts = []

    def to_dict(self):
        settings = self.settings.__dict__.copy()
        del settings['config']
        return {
            'requester': self.requester,
            'inputfile': self.inputfile,
            'id_type': self.id_type,
            'id': self.id,
            'settings': settings
        }

    def generateoptions(self):
        options = {'format': self.container.format,
                   'video': self.container.videooptions,
                   'audio': self.container.audiooptions,
                   'subtitle': self.container.subtitleoptions}

        return options

    def convert(self):
        conv = self.__class__.converter.convert(self.fullpath,
                                                self.outputfile,
                                                self.generateoptions(),
                                                preopts=self.preopts,
                                                postopts=self.postopts)
        for timecode in conv:
            pass

        return True

    def getdimensions(self):
        info = self.__class__.converter.probe(self.inputfile)
        self.height = info.video.video_height
        self.width = info.video.video_width

    def needprocessing(self):
        input_dir, filename, input_extension = parse_file(self.inputfile)
        if (input_extension.lower() in valid_input_extensions or (
                self.settings.processMP4 is True and input_extension.lower() in valid_output_extensions)) and self.output_extension.lower() in valid_output_extensions:
            return True
        else:
            return False

    def isvalidsource(self):
        input_dir, filename, input_extension = parse_file(self.inputfile)
        if input_extension.lower() in valid_input_extensions or input_extension.lower() in valid_output_extensions:
            if os.path.isfile(self.inputfile):
                return True
            else:
                return False
        else:
            return False

    def gettasks(self):
        if self.needprocessing():
            self.tasks.append('convert')
        if self.settings.tagfile:
            self.tasks.append('fetch')
            self.tasks.append('tag')
        if self.settings.relocate_moov:
            self.tasks.append('qtfs')
        if self.settings.moveto or self.settings.copyto:
            self.tasks.append('relocate')

    def fetchtags(self):
        pass


class TVJob(BaseJob):
    def __init__(self, request):
        try:
            self.season = int(request['season'])
            self.episode = int(request['episode'])
        except KeyError:
            raise Exception('Request dict should contain season number and episode number')
        super(TVJob, self).__init__(request)

    def fetchtags(self):
        return fetchers.FetchersFactory().GetFromJob(self, language=self.settings.taglanguage)

    def to_dict(self):
        return {
            'requester': self.requester,
            'inputfile': self.inputfile,
            'id_type': self.id_type,
            'id': self.id,
            'season': self.season,
            'episode': self.episode
        }


class MovieJob(BaseJob):
    def __init__(self, request):
        super(MovieJob, self).__init__(request)


class ManualJob(BaseJob):
    def __init__(self, request):
        super(ManualJob, self).__init__(request)


class JobException(Exception):
    pass


if __name__ == '__main__':
    tv = {'jobtype': 'tvshow',
          'inputfile': '/Users/Jon/Downloads/in/The.Polar.Express.(2004).1080p.BluRay.MULTI.x264-DiG8ALL.mkv',
          'original': '/Users/Jon/Downloads/in/The.Polar.Express.(2004).1080p.BluRay.MULTI.x264-DiG8ALL.mkv',
          'season': 2,
          'episode': 2,
          'id': 176941,
          'id_type': 'tvdb',
          'requester': 'sickrage',
          'settings': 'default'
          }

    movie = {
        'jobtype': 'movie',
        'inputfile': '/Users/Jon/Downloads/in/Fargo S02E01.mkv',
        'original': '/Users/Jon/Downloads/in/Fargo S02E01.mkv',
        'id': 2501,
        'id_type': 'tmdb',
        'requester': 'sickrage',
        'settings': 'defaults'
    }
    #/Users/Jon/Downloads/config/defaults.ini
    movieimdb = {
        'jobtype': 'movie',
        'inputfile': '/Users/Jon/Downloads/in/Fargo S02E01.mkv',
        'original': '/Users/Jon/Downloads/in/Fargo S02E01.mkv',
        'id': 'tt5699154',
        'id_type': 'imdb',
        'requester': 'sickrage',
        'settings': 'defaults'
    }

    tvjob = TVJob(tv)
#    tvjob.convert()

#    moviejob = MovieJob(movie)
#    imdbjob = MovieJob(movieimdb)
