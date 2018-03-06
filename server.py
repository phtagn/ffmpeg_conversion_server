#!/usr/bin/env python
from __future__ import print_function

# from post_processor import PostProcessor
import json
import os
import sys

from twisted.internet import defer, threads
from twisted.logger import Logger, textFileLogObserver, FilteringLogObserver, LogLevelFilterPredicate, LogLevel, \
    globalLogPublisher
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
            return 'Request refused: {request!r} ; {e.message}'.format(request=request, e=e)

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
        """

        :param limit: int
        """
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

    def __init__(self, job, logger=None, settings=None):
        """

        :param job: BaseJob
        :param logger: twisted.logger
        :param settings: ReadSettings
        """
        # self.log.namespace = 'RemoteConverter'
        assert isinstance(job, BaseJob)
        self.job = job
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
            log.info('Overriding default settings')
            for k, v in override.iteritems():
                if k in settings.__dict__.keys():
                    settings.__dict__[k] = v  # TODO: decode the unicode value to str
                else:
                    log.error('incorrect key {k}'.format(k=k))
        return settings

    def convert(self):
        q = SimpleJobQueue(2)
        d = q.addjob(self.converter.process, self.job.inputfile, original=self.job.original)

        if self.settings.tagfile:
            d.addCallback(self.tag)

        if self.settings.relocate_moov:
            d.addCallback(self.qtfs)

        d.addCallback(self.replicate)
        d.addCallbacks(self.logsuccess, self.logerrors)

    def isjobvalid(self):
        return self.converter.validSource(self.job.inputfile)

    def tag(self, output):
        log.debug('Tagging file {output}', output=output['output'])
        if self.job.tag(output, language=self.settings.taglanguage, artwork=self.settings.artwork,
                        thumbnail=self.settings.thumbnail):
            log.debug('File tagged successfuly')
        return output

    def qtfs(self, output):
        log.debug('Launching qtfs')
        self.converter.QTFS(output['output'])
        return output

    def replicate(self, output):
        files = self.converter.replicate(output['output'])
        log.debug('{files} succesfully moved', files=files)
        return files

    def logerrors(self, reason):
        log.error(reason.getErrorMessage())

    def logsuccess(self, _):
        log.info('{params.inputfile} succesfully converted', params=self.job)

    def refresh_plex(self):
        from autoprocess import plex
        plex.refreshPlex(self.settings, 'show')

    def refresh_sickrage(self):
        import urllib
        try:
            refresh = json.load(urllib.urlopen(self.settings.getRefreshURL(self.job.tvdb_id)))
            for item in refresh:
                log.debug(refresh[item])
        except (IOError, ValueError):
            log.exception("Couldn't refresh Sickbeard, check your autoProcess.ini settings.")


class BaseJob(object):
    def __init__(self, params):
        try:
            self.inputfile = params['inputfile']
            self.original = params['original']
        except KeyError:
            raise Exception('Request dict should contain inputfile and original')

    def tag(self, output, language='en', artwork=False, thumbnail=False):
        pass


class TVJob(BaseJob):
    def __init__(self, params):
        super(TVJob, self).__init__(params)
        try:
            self.tvdb_id = int(params['tvdb_id'])
            self.season = int(params['season'])
            self.episode = int(params['episode'])
        except KeyError:
            log.debug('Received incorrect params')
            raise Exception('Request dict should contain tvdb_id, season number and episode number')

    def tag(self, output, language='en', artwork=False, thumbnail=False):

        try:
            from tvdb_mp4 import Tvdb_mp4
            tagmp4 = Tvdb_mp4(self.tvdb_id, self.season, self.episode, self.original,
                              language=language)
            tagmp4.setHD(output['x'], output['y'])
            tagmp4.writeTags(output['output'], artwork, thumbnail)
        except:
            log.error('Tagging of {file} failed', output=output)
            return False
        log.debug('File {output.output} tagged successfully', output=output)
        return True


class MovieJob(BaseJob):
    def __init__(self, params):
        super(MovieJob, self).__init__(params)
        try:
            self.imdb_id = int(params['imdb_id'])
        except KeyError:
            raise Exception('Request dict should contain imdbid')

    def tag(self, output, language='en', artwork=False, thumbnail=False):
        try:
            from tmdb_mp4 import tmdb_mp4
            tagmp4 = tmdb_mp4(self.imdb_id, original=self.original,
                              language=language)
            tagmp4.setHD(output['x'], output['y'])
            tagmp4.writeTags(output['output'], artwork)
        except:
            log.error('Tagging of {file} failed', output=output)
        log.debug('File {output.output} tagged successfully', output=output)


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
    log = Logger()
    level = LogLevel.info
    predicate = LogLevelFilterPredicate(defaultLogLevel=level)
    observer = FilteringLogObserver(textFileLogObserver(sys.stdout), [predicate])
    globalLogPublisher.addObserver(observer)

    from twisted.internet import reactor

    r = RPCServer()
    reactor.listenTCP(7080, server.Site(r))
    reactor.run()
