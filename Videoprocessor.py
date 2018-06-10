import configuration
import logging
import os
from transitions import Machine, State
from converter.ffmpeg import FFMpeg
from converter.target import TargetContainerFactory
from converter.optiongenerator import OptionGenerator
from fetchers.fetchers import FetchersFactory
from taggers import tagger
import shutil

logging.basicConfig(filename='server.log', filemode='w', level=logging.DEBUG)
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

class VideoProcessor(object):

    def __init__(self, infile, target, config=None, tagging_info=None):
        conf = configuration.cfgmgr()

        if config:
            try:
                conf.load(config)
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

        self.fh = FileHandler(self.config)

        if self.config['File'].get('work_directory'):
            outpath = self.config['File'].get('work_directory')
        else:
            outpath = self.fh.breakdown(self.inputfile)['dir']

        self.full_work_path = os.path.join(outpath, self.fh.breakdown(self.inputfile)['file'] + '.' + self.target)

        if self.full_work_path == self.inputfile:
            self.full_work_path = os.path.join(outpath, self.fh.breakdown(self.inputfile)['file'] + '-working.' + self.target)

    @property
    def needtagging(self) -> bool:
        if self.config['Tagging']['tagfile'] is True and self.tagging_info:
            return True
        else:
            return False

    @property
    def needpostprocessing(self) -> bool:
        return False

    @property
    def needrefreshing(self) -> bool:
        return True

    @property
    def needdeploying(self):
        return True

    def do_process(self):
        """
        Processes the sourcefile into a target container
        :return:
        """
        sourcecontainer = self.ffmpeg.probe(self.inputfile)
        self.container = TargetContainerFactory(self.config, self.target).build_target_container(sourcecontainer)

    def do_convert(self):

        opts = OptionGenerator(self.config).get_options(self.container)
        for timecode in self.ffmpeg.convert(self.inputfile, self.full_work_path, opts, preopts=None, postopts=None):
            print(timecode)

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
        if os.path.isfile(self.full_work_path):
            for f in self.container.postprocess:
                f(self.full_work_path)

    def do_deploy(self):
        t = self.fh.breakdown(self.inputfile)['file']
        if self.config['File'].get('copy_to'):
            self.fh.copy(self.full_work_path, t + '.' + self.target)

        if self.config['File'].get('move_to'):
            self.fh.move(self.full_work_path)

        if self.config['File'].get('delete_original'):
            self.fh.delete_original(self.inputfile)

    def do_refresh(self):
        print('refreshing')


class FileHandler(object):

    def __init__(self, cfg):
        self.copy_to = cfg['File'].get('copy_to')
        self.move_to = cfg['File'].get('move_to')
        self.mask = cfg['File'].get('permissions')
        self.delete_original = cfg['File'].get('delete_original')

    @staticmethod
    def breakdown(filepath: os.path):

        dir, fileandext = os.path.split(filepath)
        file, ext = os.path.splitext(fileandext)

        return {'dir': dir, 'filandext': fileandext, 'file': file, 'ext': ext}

    def copy(self, infile: os.path, dst: str):
        if not self.copy_to:
            return False

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
        if not self.move_to:
            return False

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

        if videoprocessor.needtagging:
            states.append(State(name='tagged', on_enter=['do_tag']))

        #if videoprocessor.needpostprocessing:
        #    states.append(State(name='postprocessed', on_enter=['do_postprocess']))

        if videoprocessor.needdeploying:
            states.append(State(name='deployed', on_enter=['do_deploy']))

        if videoprocessor.needrefreshing:
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

