#!/usr/bin/env python
from __future__ import print_function

import json
import os
import sys

from twisted.internet import defer, threads
from twisted.logger import Logger, textFileLogObserver, FilteringLogObserver, LogLevelFilterPredicate, LogLevel, \
    globalLogPublisher
from twisted.web import xmlrpc, server

from converter.ffmpeg import FFMpegError, FFMpegConvertError
from mkvtomp4 import MkvtoMp4
from readSettings import ReadSettings


def loadsettings(inifile=None):
    settings = None

    if inifile and os.path.isfile(inifile):
        path = os.path.abspath(inifile)
        settings_dir, filename = os.path.split(path)
        try:
            settings = ReadSettings(settings_dir, filename)
            log.info('Loaded settings from file {inifile}', inifile=inifile)
            return settings
        except:
            log.error('{inifile} supplied, but could not load settings', inifile=inifile)

    if not settings:
        try:
            settings = ReadSettings(os.path.dirname(sys.argv[0]), "autoProcess.ini")
            log.info('Loaded default settings from {dir}/autoProcess.ini', dir=os.path.dirname(sys.argv[0]))
            return settings
            # return 'Loaded default settings for {path}'.format(path=os.path.dirname(sys.argv[0]))
        except Exception as e:
            raise xmlrpc.Fault(5, 'Failed loading settings or default settings, with exception {exc}'.format(
                exc=e))

# TODO: set-up alert when fails. Push notifications ? mail ?
class RPCServer(xmlrpc.XMLRPC):

    def xmlrpc_convert(self, convertinfo, inifile=None):
        """Adds a conversion job to the queue"""

        try:
            settings = loadsettings(inifile=inifile)
        except Exception as e:
            raise e

        try:
            request = json.loads(convertinfo)
            log.debug('Received request: {request!r}', request=request)
        except:
            raise xmlrpc.Fault(1, 'Request refused, params should be a json object')

        try:
            params = FactoryJob.getjob(request)
        except Exception as e:
            raise xmlrpc.Fault(2, 'Request refused: {request!r} ; {e.message}'.format(request=request, e=e))

        rc = RemoteConverter(params, settings=settings)

        if rc.isjobvalid():
            log.info('Accepted job {params.inputfile}', params=params)
            d = rc.convert()
            return d
            # return 'Request accepted: {params.inputfile}'.format(params=params)
        else:
            log.error('{params.inputfile} is not a valid source', params=params)
            raise xmlrpc.Fault(4, 'Request refused: {params.inputfile} is not a valid source'.format(params=params))


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
        d.addCallback(self._endjob)
        return d

        # return reason

class RemoteConverter(object):
    """Remote Converter expects """

    def __init__(self, job, settings):
        """

        :param job: BaseJob
        :param settings: ReadSettings
        """
        # self.log.namespace = 'RemoteConverter'
        assert isinstance(job, BaseJob)
        self.job = job
        assert isinstance(settings, ReadSettings)
        self.settings = settings
        self.converter = MkvtoMp4(self.settings)
        self.status = {}

    def convert(self):
        q = SimpleJobQueue(2)

        d = q.addjob(self.converter.process, self.job.inputfile, original=self.job.original)

        d.addCallbacks(self.getresults, self.handleerror)

        if self.settings.tagfile:
            d.addCallbacks(self.tag, self.handleerror)

        if self.settings.relocate_moov:
            d.addCallbacks(self.qtfs, self.handleerror)

        d.addCallbacks(self.replicate, self.handleerror)

        if self.settings.Plex['refresh']:
            d.addCallbacks(self.refresh_plex, self.handleerror)

        if self.settings.Sickbeard['api_key']:
            d.addCallbacks(self.refresh_sickrage, self.handleerror)

        d.addCallbacks(self.logsuccess, self.logerrors)
        return d

    def isjobvalid(self):
        return self.converter.validSource(self.job.inputfile)

    def getresults(self, output):
        self.job.outputfile = output['output']
        self.job.x = output['x']
        self.job.y = output['y']

    def tag(self, output):
        log.debug('Tagging file {output}', output=output['output'])
        try:
            result = self.job.tag(output, language=self.settings.taglanguage, artwork=self.settings.artwork,
                                  thumbnail=self.settings.thumbnail)
        except:
            raise TagError

        if result:
            log.debug('File tagged successfuly')
            self.status['tag'] = 'success'
        return output

    def qtfs(self, output):
        log.debug('Launching qtfs')
        try:
            self.outputfile = self.converter.QTFS(self.outputfile)
        except:
            raise Exception

        self.status['qtfs'] = 'success'
        return output

    def replicate(self, output):
        files = self.converter.replicate(output['output'])
        log.debug('{files!r} succesfully moved', files=files)
        self.status['replicate'] = files
        return files

    def handleerror(self, reason):
        if reason.check(FFMpegError, FFMpegConvertError):
            log.error('A non recoverable error occurred {err}'.format(err=reason.getErrorMessage()))
            raise reason.value
        else:
            log.error('Error !! {err}'.format(err=reason.getErrorMessage()))

    def logsuccess(self, _):
        log.info('{params.inputfile} succesfully converted', params=self.job)
        return self.status

    def logerrors(self, reason):
        log.error(reason.getErrorMessage())
        return reason.getErrorMessage()

    def refresh_plex(self, _):
        log.info('Refreshing plex')
        from autoprocess import plex
        plex.refreshPlex(self.settings, 'show')
        self.status['Plex'] = 'success'

    def refresh_sickrage(self, _):
        import urllib
        try:
            refresh = json.load(urllib.urlopen(self.settings.getRefreshURL(self.job.tvdb_id)))
            for item in refresh:
                log.debug(refresh[item])
        except (IOError, ValueError):
            log.error("Couldn't refresh Sickbeard, check your autoProcess.ini settings.")





class FactoryJob(object):
    def __init__(self):
        pass

    @staticmethod
    def getjob(request):
        try:
            if request['params']['jobtype'] == 'tvshow':
                return TVJob(request)
            if request['params']['jobtype'] == 'movie':
                return MovieJob(request)
            if request['params']['jobtype'] == 'manual':
                return ManualJob(request)
        except Exception as e:
            raise e
        #Exception('No such jobtype, accepted types are tvshow, movie, and manual')


class TagError(Exception):
    pass


if __name__ == '__main__':
    log = Logger()
    level = LogLevel.debug
    predicate = LogLevelFilterPredicate(defaultLogLevel=level)
    observer = FilteringLogObserver(textFileLogObserver(sys.stderr), [predicate])
    globalLogPublisher.addObserver(observer)

    from twisted.internet import reactor

    r = RPCServer()
    xmlrpc.addIntrospection(r)
    port = os.getenv('MP4PORT', 7080)
    if isinstance(port, basestring) and port.isdigit():
        port = int(port)

    reactor.listenTCP(port, server.Site(r))
    reactor.run()
