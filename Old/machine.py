import configuration
import logging
import os
from transitions import Machine, State
from converter import FFMpeg
from containers import ContainerFactory, UnsupportedContainer
from fetchers import FetchersFactory
from taggers import tagger
import shutil

logging.basicConfig(filename='server.log', filemode='w', level=logging.DEBUG)
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

class VideoProcessor(object):
    states = ['initialized',
              State(name='probed', on_enter=['do_probe']),
              State(name='processed', on_enter=['do_process']),
              State(name='converted', on_enter=['do_convert']),
              State(name='tagged', on_enter=['do_tag']),
              State(name='postprocessed', on_enter=['do_postprocess']),
              State(name='deployed', on_enter=['do_deploy']),
              State(name='refreshed', on_enter=['do_refresh'])
              ]

#    transitions = [
#        {'trigger': 'probe', 'source': 'initialized', 'dest': 'probed'},
#        {'trigger': 'process', 'source': 'probed', 'dest': 'processed'},
#        {'trigger': 'convert', 'source': 'processed', 'dest': 'converted'},
#        {'trigger': 'tag', 'source': 'converted', 'dest': 'tagged', 'conditions': 'need_tagging'},
#        {'trigger': 'postprocess', 'source': ['converted', 'tagged'], 'dest': 'postprocess'},
#        {'trigger': 'deploy', 'source': ['converted', 'tagged', 'postprocessed'], 'dest': 'deployed'},
#        {'trigger': 'refresh', 'source': 'deployed', 'dest': 'refreshed'},
#        {'trigger': 'idle', 'source': 'deployed', 'dest': 'initialized'}
#    ]

    def __init__(self, request):
        # Check that we have everything we need
        conf = configuration.cfgmgr()
        if request.get_parser('configname', None):
            conf.load(request['configname'])
            self.config = conf.cfg
        else:
            self.config = conf.defaultconfig

        conf.save('defaults.ini')
        if 'infile' in request:
            path = os.path.abspath(request['infile'])

            if os.path.isfile(path):
                self.fullinpath = path
                self.indir, f = os.path.split(path)
                self.infile, self.inext = os.path.splitext(f)
                self.inext = self.inext[1:]
            else:
                raise IOError(f'File {path} does not exist')
        else:
            raise Exception('Request should contain the inputfile.')

        self.showid = request['id']
        self.id_type = request['id_type']
        self.season = request.get_parser('season', None)
        self.episode = request.get_parser('episode', None)
        self.language = 'en'

        if 'target' in request:
            if request['target'].lower() not in ContainerFactory.containers:
                log.critical(f'Target {request["target"]} not available. '
                             f'Supported containers are {", ".join(SourceContainerFactory.containers.keys())}')
                raise UnsupportedContainer
            self.container = ContainerFactory.get_parser(request['target'].lower(), self.config)
        else:
            raise Exception('Target container (e.g. mp4) should be in the request')

        self.ffmpeg = FFMpeg(self.config['FFMPEG'].get_parser('ffmpeg'), self.config['FFMPEG'].get_parser('ffprobe'))

        if self.config['File'].get_parser('output_directory'):
            outpath = self.config['File'].get_parser('output_directory')
        else:
            outpath = self.indir



        self.fulloutpath = os.path.join(outpath, self.infile + self.container.extension)
        if self.fulloutpath == self.fullinpath:
            self.fulloutpath += '.working'

        self.fileinfo = None

        self.machine = Machine(model=self, states=VideoProcessor.states, initial='initialized')
        self.machine.add_ordered_transitions(['initialized', 'probed', 'processed', 'converted', 'tagged', 'postprocessed', 'deployed', 'refreshed'])

    def do_probe(self):
        self.fileinfo = self.ffmpeg.probe(self.fullinpath)

    def do_process(self):
        self.container.processstreams(self.fileinfo)

    def do_convert(self):
        opts = self.container.parse_options()
        for timecode in self.ffmpeg.convert(self.fullinpath, self.fulloutpath, opts, preopts=self.container.preopts, postopts=self.container.postopts):
            print(timecode)

    def do_tag(self):

        if self.config['Tagging'] is False:
            print('Nothing to do here')
        ftch = FetchersFactory.getfetcher(self.config, self.showid, self.id_type, season=self.season, episode=self.episode)
        tags = ftch.gettags()

        if tags.poster_url and self.config['Tagging'].get_parser('download_artwork') is True:
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
        if self.config['File'].get_parser('copy_to'):
            for d in self.config['File'].get_parser('copy_to'):
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

        if self.config['File'].get_parser('move_to'):
            d = self.config['File'].get_parser('movet_to')
            if os.path.isdir(d):
                if os.access(d, os.W_OK):
                    try:
                        os.rename(self.fullinpath, os.path.join(d, f'{self.infile}.{self.container.extension}'))
                    except:
                        log.exception('Error while moving file')
                else:
                    log.error('Directory %s is not writeable', d)
            else:
                log.error('Path %s is not a directory', d)



    def do_refresh(self):
        print('refreshing')

if __name__ == '__main__':
    showid = 75978
    id_type = 'tvdb_id'

    req = {'infile': '/Users/jon/Downloads/family.guy.s16e19.720p.web.x264-tbs.mkv',
           'configname': 'testouille.ini',
           'target': 'MP4',
           'id': showid,
           'id_type': id_type,
           'season': 16,
           'episode': 18
           }

    VP = VideoProcessor(req)

while True:
    VP.next_state()
    if VP.state == 'refreshed':
        break

print('yeah')

