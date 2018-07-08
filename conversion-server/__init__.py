import configuration
import os
from flask import Flask, jsonify, abort, request
import logging
import sys


app = Flask(__name__)

log = logging.getLogger()
log.setLevel(logging.INFO)
sh = logging.StreamHandler(sys.stdout)
sh.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s - %(message)s')
sh.setFormatter(formatter)
log.addHandler(sh)


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
    return jsonify(os.listdir('config'))


@app.route('/config/default', methods=['GET'])
def defaultconfig():
    cfgmgr = configuration.cfgmgr()
    return jsonify(cfgmgr.defaultconfig)


@app.route('/config/<string:configfile>', methods=['GET'])
def configfile(configfile):
    cfgmgr = configuration.cfgmgr()

    if os.path.exists(os.path.join('config', configfile)):
        cfgmgr.load(config=configfile)
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


if __name__ == '__main__':
    app.run(use_debugger=True, use_reloader=True)
