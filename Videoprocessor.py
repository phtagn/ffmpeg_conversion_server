import configuration
import logging
import os
from transitions import Machine, State
from converter import FFMpeg
from containers import ContainerFactory, UnsupportedContainer
from fetchers import FetchersFactory
import tagger
import shutil

logging.basicConfig(filename='server.log', filemode='w', level=logging.DEBUG)
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

class VideoProcessor(object):

    def __init__(self, infile, target, config, tagging_info=None):
        conf = configuration.cfgmgr()
        self._fileinfo = None
        if config:
            try:
                conf.load(config)
                self._config = conf.cfg
            except:
                raise Exception('Config %s is not available in config directory', config)
        else:
            self._config = conf.defaultconfig

        path = os.path.abspath(infile)
        if os.path.isfile(path):
            self._infile = infile
        else:
            raise IOError(f'File {path} does not exist')

        self._tagging_info = tagging_info

        if target.lower() not in ContainerFactory.containers:
            log.critical(f'Target {target} not available. '
                        f'Supported containers are {", ".join(ContainerFactory.containers.keys())}')
            raise UnsupportedContainer
        self._container = ContainerFactory.get(target.lower(), self.config)

    @property
    def config(self):
        return self._config

    @property
    def infile(self):
        return self._infile

    @property
    def indir(self):
        indir, _ = os.path.splitext(self.infile)
        return indir

    @property
    def input_ext(self):
        _, ext = os.path.splitext(self.infile)
        return ext[1:]

    @property
    def container(self):
        return self._container

    @property
    def fulloutpath(self):
        if self.config['File'].get('output_directory'):
            outpath = self.config['File'].get('output_directory')
        else:
            outpath = self.indir

        fulloutpath = os.path.join(outpath, self.infile + self.container.extension)

        if fulloutpath == self.infile:
            fulloutpath += '.working'

        return fulloutpath

    @property
    def tagging_info(self):
        return self._tagging_info

    @property
    def fileinfo(self):
        if not self._fileinfo:
            self._fileinfo = self.ffmpeg.probe(self.infile)

        return self._fileinfo

    @property
    def showid(self):
        return self.tagging_info.get('id', None)

    @property
    def id_type(self) -> str:
        return self.tagging_info.get('id_type', None)

    @property
    def season(self) -> int:
        return self.tagging_info.get('season', None)

    @property
    def episode(self) -> int:
        return self.tagging_info.get('episode', None)

    @property
    def ffmpeg(self):
        return FFMpeg(self.config['FFMPEG'].get('ffmpeg'), self.config['FFMPEG'].get('ffprobe'))

    @property
    def needtagging(self) -> bool:
        if self.config['Tagging']['tagfile'] is True and self.tagging_info:
            return True
        else:
            return False

    @property
    def needprocessing(self) -> bool:
        if self.container.ffmpeg_format in self.fileinfo.format.format and not self.container.process_same:
            return False
        else:
            return True

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
        self.container.processstreams(self.fileinfo)

    def do_convert(self):
        opts = self.container.parse_options()
        for timecode in self.ffmpeg.convert(self.infile, self.fulloutpath, opts, preopts=self.container.preopts, postopts=self.container.postopts):
            print(timecode)

    def do_tag(self):

        ftch = FetchersFactory.getfetcher(self.config, self.showid, self.id_type, season=self.season, episode=self.episode)
        tags = ftch.gettags()

        if tags.poster_url and self.config['Tagging'].get('download_artwork') is True:
            posterfile = ftch.downloadArtwork(tags.poster_url)
        else:
            posterfile = None

        t = tagger.TaggerFactory.get(self.container.name, tags, self.fulloutpath, artworkfile=posterfile)
        if t:
            t.writetags()
        else:
            log.info('Tagging is not supported for container %s at this time, skipping', self.container.name)

    def do_postprocess(self):
        if os.path.isfile(self.fulloutpath):
            for f in self.container.postprocess:
                f(self.fulloutpath)

    def do_deploy(self):
        if self.config['File'].get('copy_to'):
            for d in self.config['File'].get('copy_to'):
                if os.path.isdir(d):
                    if os.access(d, os.W_OK):
                        try:
                            shutil.copy2(self.fulloutpath, os.path.join(d, f'{self.infile}.{self.container.extension}'))
                        except:
                            raise Exception('Error while copying file')
                    else:
                        log.error('Directory %s is not writeable', d)
                else:
                    log.error('Path %s is not a directory', d)

        if self.config['File'].get('move_to'):
            d = self.config['File'].get('movet_to')
            if os.path.isdir(d):
                if os.access(d, os.W_OK):
                    try:
                        os.rename(self.fulloutpath, os.path.join(d, f'{self.infile}.{self.container.extension}'))
                    except:
                        log.exception('Error while moving file')
                else:
                    log.error('Directory %s is not writeable', d)
            else:
                log.error('Path %s is not a directory', d)

    def do_refresh(self):
        print('refreshing')

class MachineFactory(object):

    @staticmethod
    def get(infile, target, config, tagging_info=None):
        videoprocessor = VideoProcessor(infile, target, config, tagging_info=tagging_info)
        machine = Machine(model=videoprocessor, initial='rest')
        states = ['rest']

        if videoprocessor.needprocessing:
            states.append(State(name='processed', on_enter=['do_process']))
            states.append(State(name='converted', on_enter=['do_convert']))

        if videoprocessor.needtagging:
            states.append(State(name='tagged', on_enter=['do_tag']))

        if videoprocessor.needpostprocessing:
            states.append(State(name='postprocessed', on_enter=['do_postprocess']))

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

    infile = '/Users/jon/Downloads/family.guy.s16e19.720p.web.x264-tbs.mkv'
    configname = 'testouille.ini'
    target = 'mkv'
    info = {'id': showid,
            'id_type': id_type,
            'season': 16,
            'episode': 18
           }

    VP = MachineFactory.get(infile=infile, config=configname, target=target, tagging_info=None)

    print(VP.state)
while True:
    VP.next_state()
    print(VP.state)
    if VP.state == 'refreshed':
        break


print('yeah')

