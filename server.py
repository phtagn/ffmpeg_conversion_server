#!/usr/bin/env python
from __future__ import print_function

# from post_processor import PostProcessor
# from logging.config import fileConfig
import json
import os
import sys

from twisted.internet import defer, threads
from twisted.logger import Logger, textFileLogObserver
from twisted.web import xmlrpc, server

from mkvtomp4 import MkvtoMp4
from readSettings import ReadSettings


class RPCServer(xmlrpc.XMLRPC):

    def xmlrpc_convert(self, convertinfo):
        try:
            request = json.loads(convertinfo)
            log.debug('Received request: {request!r}', request=request)
        except:
            return 'Request refused, params should be a json object'

        try:
            params = FactoryJob.getjob(request['params'])
        except Exception as e:
            return 'Request {request!r} refused: {e.message}'.format(request=request, e=e)

        try:
            settings = request['settings']
        except KeyError:
            settings = None

        rc = RemoteConverter(params, settings=settings)

        if rc.isjobvalid():
            log.info('Accepted job {params.inputfile}', params=params)
            rc.convert()
            return 'Request accepted: {params.inputfile}'.format(params=params)
        else:
            log.error('{params.inputfile} is not a valid source', params=params)
            return 'Request refused: {params.inputfile} is not a valid source'.format(params=params)


class Singleton(type):
    instance = None

    def __call__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super(Singleton, cls).__call__(*args, **kwargs)
        return cls.instance


class SimpleJobQueue(object):
    __metaclass__ = Singleton

    def __init__(self, limit):
        self.limit = limit
        self.processing = 0
        self.processlist = list()

    def addjob(self, f, *args, **kwargs):
        job = (f, args, kwargs)
        d = defer.Deferred()
        d.addCallback(self._excjob, job)
        self.processlist.append(d)
        self._runjob()
        return d

    # TODO: handle cancellation
    # def cancel(self):
    #    for d in self.processlist:
    #        d.cancel

    def _runjob(self):
        if self.processing < self.limit and len(self.processlist) > 0:
            self.processlist.pop().callback('')

    def _endjob(self, result):
        self.processing -= 1
        self._runjob()
        return result

    def _excjob(self, _, job):
        f, args, kwargs = job
        self.processing += 1
        d = threads.deferToThread(f, *args, **kwargs)
        d.addBoth(self._endjob)
        return d


class RemoteConverter(object):
    """Remote Converter expects """

    def __init__(self, params, logger=None, settings=None):
        self.log = logger if logger else Logger(observer=textFileLogObserver(sys.stdout), namespace='RemoteConverter')
        self.log.namespace = 'RemoteConverter'
        assert isinstance(params, BaseJob)
        self.params = params
        self.settings = self._overridesettings(settings)
        self.converter = MkvtoMp4(self.settings)

    def _overridesettings(self, override):
        try:
            settings = ReadSettings(os.path.dirname(sys.argv[0]), "autoProcess.ini")
            # settings = ReadSettings('/Users/Jon/Downloads/config/', 'autoProcess.ini')
        except:
            raise IOError('Could not find settings file')

        if override is not None:
            assert isinstance(override, dict)
            self.log.info('Overriding default settings')
            for k, v in override.iteritems():
                if k in settings.__dict__.keys():
                    settings.__dict__[k] = v  # TODO: decode the unicode value to str
                else:
                    self.log.error('incorrect key {k}'.format(k))
        return settings

    def convert(self):
        q = SimpleJobQueue(2)
        d = q.addjob(self.converter.process, self.params.inputfile, original=self.params.original)

        if self.settings.tagfile:
            d.addCallback(self.tag)

        if self.settings.relocate_moov:
            d.addCallback(self.qtfs)

        d.addCallback(self.replicate)
        d.addCallbacks(self.logsuccess, self.logerrors)

    def isjobvalid(self):
        return self.converter.validSource(self.params.inputfile)

    def tag(self, output):
        self.log.debug('Tagging file {output.output}', output=output)
        if isinstance(self.params, MovieJob):
            try:
                from tmdb_mp4 import tmdb_mp4
                tagmp4 = tmdb_mp4(self.params.imdb_id, original=self.params.original,
                                  language=self.settings.taglanguage)
                tagmp4.setHD(output['x'], output['y'])
                tagmp4.writeTags(output['output'], self.settings.artwork)
            except:
                self.log.error('Tagging of {file} failed', output=output)

        if isinstance(self.params, TVJob):
            self.log.debug('Tagging TV Show')
            try:
                from tvdb_mp4 import Tvdb_mp4
                tagmp4 = Tvdb_mp4(self.params.tvdb_id, self.params.season, self.params.episode, self.params.original,
                                  language=self.settings.taglanguage)
                tagmp4.setHD(output['x'], output['y'])
                tagmp4.writeTags(output['output'], self.settings.artwork, self.settings.thumbnail)
            except:
                self.log.error('Tagging of {file} failed', output=output)
        self.log.debug('File {output.output} tagged successfully', output=output)
        return output

    def qtfs(self, output):
        self.log.debug('Launching qtfs')
        self.converter.QTFS(output['output'])
        return output

    def replicate(self, output):
        files = self.converter.replicate(output['output'])
        self.log.debug('{files} succesfully moved', files=files)
        return files

    def logerrors(self, reason):
        self.log.error(reason.getErrorMessage())

    def logsuccess(self, _):
        self.log.info('{params.inputfile} succesfully converted', params=self.params)

    # TODO: Subtitles


class BaseJob(object):
    def __init__(self, params):
        try:
            self.inputfile = params['inputfile']
            self.original = params['original']
        except KeyError:
            raise Exception('Request dict should contain inputfile and original')


class TVJob(BaseJob):
    def __init__(self, params):
        super(TVJob, self).__init__(params)
        try:
            self.tvdb_id = int(params['tvdb_id'])
            self.season = int(params['season'])
            self.episode = int(params['episode'])
        except KeyError:
            raise Exception('Request dict should contain tvdb_id, season number and episode number')


class MovieJob(BaseJob):
    def __init__(self, params):
        super(MovieJob, self).__init__(params)
        try:
            self.imdb_id = int(params['imdb_id'])
        except KeyError:
            raise Exception('Request dict should contain imdbid')


class ManualJob(BaseJob):
    pass  # TODO: Ability to send a manual job


class FactoryJob(object):
    def __init__(self):
        pass

    @staticmethod
    def getjob(params):
        if params['jobtype'] == 'tvshow':
            return TVJob(params)
        if params['jobtype'] == 'movie':
            return MovieJob(params)
        if params['jobtype'] == 'manual':
            return ManualJob(params)
        raise Exception('No such jobtype, accepted types are tvshow, movie, and manual')


if __name__ == '__main__':
    log = Logger(observer=textFileLogObserver(sys.stdout), namespace='RemoteConverter')

    from twisted.internet import reactor

    r = RPCServer()
    reactor.listenTCP(7080, server.Site(r))
    reactor.run()
