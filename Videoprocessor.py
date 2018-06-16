import configuration
import logging
import os
from transitions import Machine, State
from converter.ffmpeg import FFMpeg
from converter.target import TargetContainerFactory
from converter.optiongenerator import OptionGenerator
from fetchers.fetchers import FetchersFactory
from taggers import tagger
from helpers.helpers import breakdown
import shutil

logging.basicConfig(filename='server.log', filemode='w', level=logging.DEBUG)
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class VideoProcessor(object):

    def __init__(self, infile: str, target: str, config: str=None, overrides: dict=None, tagging_info: dict = None, notify: list=None):
        """
        Videoprocessor contains the methods to process a video from start to finish. The steps are :
        1) Analyse the input file to determine the source container, and create the theoretical target container
        2) Convert the input file into the output file
        3) Tag the output file
        4) Postprocess, e.g. for mp4 do qtfaststart
        5) Deploy the output file to its destination
        6) Notify various apps of the
        :param infile: path to the input file
        :param target: extension of container, e.g. mp4, mkv
        :param config: name of the configuration file, relative to the config directory
        :param overrides: a dictionary containing overrides to the configuration file
        :param tagging_info: a dictionary in the same form as the config file. Does not need to contain all
        the configuration file entries, just those you want to override
        :param notify: a dictionary holding the list of applications to notify
        """
        conf = configuration.cfgmgr()

        if config:
            try:
                conf.load(config, overrides=overrides)
                self.config = conf.cfg
            except:
                raise Exception('Config %s is not available in config directory', config)
        else:
            self.config = conf.defaultconfig

        if target in self.config['Containers'].keys():
            self.target = target
        else:
            raise Exception(f'Unsupported container, valid containers are {self.config.keys()}')

        path = os.path.abspath(infile)
        if os.path.isfile(path):
            self.inputfile = path
        else:
            raise IOError(f'File {path} does not exist')

        self.tagging_info = tagging_info

        self.ffmpeg = FFMpeg(self.config['FFMPEG'].get('ffmpeg'), self.config['FFMPEG'].get('ffprobe'))

        self.fh = FileHandler(copy_to=self.config['Files'].get('copy_to'),
                              move_to=self.config['Files'].get('move_to'),
                              permissions=self.config['Files'].get('permissions'),
                              delete=self.config['Files'].get('delete_original'))

        if self.config['File'].get('work_directory'):
            outpath = self.config['File'].get('work_directory')
        else:
            outpath = breakdown(self.inputfile)['dir']

        self.full_work_path = os.path.join(outpath, breakdown(self.inputfile)['file'] + '.' + self.target)

        if self.full_work_path == self.inputfile:
            self.full_work_path = os.path.join(outpath, breakdown(self.inputfile)['file'] + '-working.' + self.target)

    def do_process(self):
        """
        Processes the sourcefile into a target container
        :return: None
        """
        source_container = self.ffmpeg.probe(self.inputfile)
        self.container = TargetContainerFactory(self.config, self.target).build_target_container(source_container)

    def do_convert(self):
        """
        Do the converion, i.e. call ffmpeg to actually convert the file.
        :return: None
        """
        opts = OptionGenerator(self.config).get_options(self.container)
        try:
            for timecode in self.ffmpeg.convert(self.inputfile, self.full_work_path, opts, preopts=None, postopts=None):
                print(timecode)
        except Exception as e:
            log.critical('Conversion failed with message %s', e)
            self.full_work_path = None

    def do_tag(self):

        _id = self.tagging_info.get('id', None)
        id_type = self.tagging_info.get('id_type', None)
        season = self.tagging_info.get('season', None)
        episode = self.tagging_info.get('episode', None)
        language = self.config['Languages'].get('tagging')

        if season:
            fetcher = self.config['Tagging'].get('preferred_show_tagger', 'tvdb')
        else:
            fetcher = self.config['Tagging'].get('preferred_movie_tagger', 'tmdb')

        ftch = FetchersFactory.getfetcher(fetcher, _id, id_type, language=language, season=season, episode=episode)
        tags = ftch.gettags()

        if tags.poster_url and self.config['Tagging'].get('download_artwork') is True:
            posterfile = ftch.downloadArtwork(tags.poster_url)
        else:
            posterfile = None

        t = tagger.TaggerFactory.get_tagger(self.container.format.format_name, tags, self.full_work_path, artworkfile=posterfile)
        if t:
            t.writetags()
        else:
            log.info('Tagging is not supported for container %s at this time, skipping', self.container.format.format_name)

    def do_postprocess(self):
        if not self.full_work_path:
            log.critical('Postrprocessing did not occur, because conversion failed')
            return False

        from postprocesses import PostProcessorFactory
        try:
            postprocesses = PostProcessorFactory.get_post_processors(self.config['Containers'][target].get('post_processors'))
        except:
            log.info('No post processing needed')
            postprocesses = None

        if postprocesses:
            for postprocess in postprocesses:
                postprocess.process()

    def do_deploy(self):
        t = breakdown(self.inputfile)['file']
        if self.config['File'].get('copy_to'):
            self.fh.copy(self.full_work_path, t + '.' + self.target)

        if self.config['File'].get('move_to'):
            self.fh.move(self.full_work_path)

        if self.config['File'].get('delete_original'):
            self.fh.delete_original(self.inputfile)

    def do_refresh(self):
        print('refreshing')


class FileHandler(object):

    def __init__(self, copy_to=None, move_to=None, permissions=None, delete: bool=None):
        self.copy_to = copy_to
        self.move_to = move_to
        self.mask = permissions
        self.delete = delete

    def copy(self, infile: os.path, dst: str):
        for d in self.copy_to:
            if os.path.isdir(d):
                if os.access(d, os.W_OK):
                    try:
                        shutil.copy2(infile, os.path.join(d, dst))
                    except:
                        raise Exception('Error while copying file')
                else:
                    log.error('Directory %s is not writeable', d)
            else:
                log.error('Path %s is not a directory', d)
            log.info('%s copied to folder(s)  %s', infile, ' ,'.join(d))

        return True

    def move(self, src: os.path, dst: os.path):

        if os.path.isdir(self.move_to):
            if os.access(self.move_to, os.W_OK):
                try:
                    os.rename(src, dst)
                except:
                    log.exception('Error while moving file')
            else:
                log.error('Directory %s is not writeable', self.move_to)
        else:
            log.error('Path %s is not a directory', self.move_to)

    def delete_original(self, infile: os.path):
        try:
            os.chmod(infile, int("0777", 8))
        except:
            log.debug('File maybe read only')

        if os.path.exists(infile):
            try:
                os.remove(infile)
            except:
                log.exception('Original file %s could not be deleted', infile)
                return False
        return True


class MachineFactory(object):

    @staticmethod
    def get(infile, target, config, tagging_info=None):
        videoprocessor = VideoProcessor(infile, target, config, tagging_info=tagging_info)
        machine = Machine(model=videoprocessor, initial='rest')
        states = ['rest']

        states.append(State(name='processed', on_enter=['do_process']))
        states.append(State(name='converted', on_enter=['do_convert']))
        states.append(State(name='tagged', on_enter=['do_tag']))
        states.append(State(name='postprocessed', on_enter=['do_postprocess']))
        states.append(State(name='deployed', on_enter=['do_deploy']))
        states.append(State(name='refreshed', on_enter=['do_refresh']))

        machine.add_states(states)
        machine.add_ordered_transitions()

        return videoprocessor

if __name__ == '__main__':
    showid = 75978
    id_type = 'tvdb_id'
    tagging_info = {'id': 75978, 'id_type': 'tvdb_id', 'season': 16, 'episode': 19}
    infile = '/Users/jon/Downloads/family.guy.s16e19.720p.web.x264-tbs.mkv'
    configname = 'defaults.ini'
    target = 'mp4'
    info = {'id': showid,
            'id_type': id_type,
            'season': 16,
            'episode': 18
           }

    VP = MachineFactory.get(infile=infile, config=configname, target=target, tagging_info=tagging_info)

    print(VP.state)
while True:
    VP.next_state()
    print(VP.state)
    if VP.state == 'refreshed':
        break


print('yeah')

