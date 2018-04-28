import json
import os
import sys

from klein import Klein
from twisted.internet import defer, threads

from jobs import BaseJob, TVJob, MovieJob


class SimpleJobQueue(object):
    limit = 2
    processing = 0
    processlist = list()

    @classmethod
    def addjob(cls, f, *args, **kwargs):
        job = (f, args, kwargs)
        d = defer.Deferred()
        d.addCallback(cls._excjob, job)
        cls.processlist.append(d)
        cls._runjob()
        return d

    # TODO: handle cancellation
    # def cancel(self):
    #    for d in self.processlist:
    #        d.cancel

    @classmethod
    def _runjob(cls):
        if cls.processing < cls.limit and len(cls.processlist) > 0:
            cls.processlist.pop().callback('')

    @classmethod
    def _endjob(cls, result):
        cls.processing -= 1
        cls._runjob()
        return result

    @classmethod
    def _excjob(cls, _, job):
        f, args, kwargs = job
        cls.processing += 1
        d = threads.deferToThread(f, *args, **kwargs)
        d.addCallback(cls._endjob)
        return d


class AutomatorServer(object):
    app = Klein()
    jobsdict = {}
    maxjobs = 2
    defaultsettings = os.path.join(os.path.dirname(sys.argv[0]), "autoProcess.ini")
    jobqueue = SimpleJobQueue()
    jobqueue.limit = maxjobs

    with app.subroute('/config') as config:
        @config.route('/maxjobs', methods=['PUT'])
        def setmaxjobs(self, request):
            content = json.loads(request.content.read())
            self.__class__.maxjobs = content['maxjobs']
            self.__class__.jobqueue.limit = self.__class__.maxjobs

        @config.route('/maxjobs', methods=['GET'])
        def getmaxjobs(self, request):
            return self.__class__.maxjobs

        @config.route('/defaultsettings.py', methods=['GET'])
        def getdefaultsettings(self, request):
            return b'toto'

    @app.route('/jobs', methods=['POST'])
    def createjob(self, request):
        content = json.loads(request.content.read())
        if 'settings' not in content:
            content['settings'] = self.__class__.defaultsettings

        if content['jobtype'] == 'tv':
            job = TVJob(content)
        elif content['jobtype'] == 'movie':
            job = MovieJob(content)
        else:
            raise Exception('Unsupported jobtype')

        self.__class__.jobsdict[job.jobid] = job
        self.jobqueue.addjob(self.convert, job)
        request.setResponseCode(201)
        return json.dumps({'jobid': job.jobid})

    def convert(self, job):
        assert isinstance(job, BaseJob)
        print(job.inputfile, job.id, job.id_type)

    @app.route('/jobs', methods=['GET'])
    def listjob(self, request):
        thelist = {}
        for jobid in self.__class__.jobsdict.keys():
            thelist[jobid] = self.__class__.jobsdict[jobid].inputfile

        if not thelist:
            request.setResponseCode(204)
        return json.dumps(thelist)

    @app.route('/jobs/<int:jobid>')
    def getjobdetails(self, request, jobid):
        content = request.content.read()
        return json.dumps(self.__class__.jobsdict[jobid].to_dict())


if __name__ == '__main__':
    server = AutomatorServer()
    server.app.run('localhost', 7080)
