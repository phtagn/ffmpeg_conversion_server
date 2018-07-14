from flask import Flask, jsonify, abort, request
from waitress import serve
import os
import sys
import logging

log = logging.getLogger('waitress')
log.setLevel(logging.DEBUG)
sh = logging.StreamHandler(sys.stdout)
sh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)s - %(message)s')
sh.setFormatter(formatter)
log.addHandler(sh)


def create_app():
    import configuration
    app = Flask(__name__, instance_relative_config=True)

    @app.route('/debug/', methods=['GET'])
    def debuglevel():
        if log.getEffectiveLevel() == logging.DEBUG:
            return jsonify('debug')
        elif log.getEffectiveLevel() == logging.INFO:
            return jsonify('info')

    @app.route('/debug/', methods=['POST'])
    def setdebuglevel():
        if 'debuglevel' in request.args:
            debuglevel = request.args['debuglevel']
        else:
            abort(404)

        if debuglevel.lower() == 'debug':
            log.setLevel(logging.DEBUG)
            sh.setLevel(logging.DEBUG)
        elif debuglevel.lower() == 'info':
            log.setLevel(logging.INFO)
            sh.setLevel(logging.INFO)
        elif debuglevel.lower() in ['warning', 'warn']:
            log.setLevel(logging.WARNING)
            sh.setLevel(logging.WARNING)

        return jsonify({'Response': f'Debug level set to {debuglevel.upper()}'})

    @app.route('/config', methods=['GET'])
    def listconfig():

        return jsonify(
                os.listdir(
                os.path.join(
                os.path.abspath(os.path.dirname(sys.argv[0])), 'config')))

    @app.route('/config/default', methods=['GET'])
    def defaultconfig():
        cfgmgr = configuration.CfgMgr()
        return jsonify(cfgmgr.defaultconfig)

    @app.route('/config/<string:configfile>', methods=['GET'])
    def configfile(configfile):
        cfgmgr = configuration.CfgMgr()

        conf = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), 'config', configfile)
        if os.path.exists(conf):
            cfgmgr.load(config=conf)
            return jsonify(cfgmgr.cfg)
        else:
            abort(404)

    @app.route('/job', methods=['GET', 'POST'])
    def add_job():
        import Videoprocessor

        if request.method == 'POST':
            from multiprocessing import Process
            content = request.json
            inputfile = content.get('inputfile')
            config = content.get('config')
            target = content.get('target')
            tagging_info = content.get('tagging_info')

            VP = Videoprocessor.MachineFactory.get(infile=inputfile, config=config, target=target,
                                                   tagging_info=tagging_info)

            p = Process(target=Videoprocessor.process, args=(VP,))
            p.start()
            return jsonify({'Response': True})

    return app


def main():
    serve(create_app(), listen='*:5000')


if __name__ == '__main__':
    main()
    # app.run(use_debugger=True, use_reloader=True)
