
import configuration
import os
from flask import Flask, jsonify, abort, request
app = Flask(__name__)

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

        VP = Videoprocessor.MachineFactory.get(infile=inputfile, config=config, target=target, tagging_info=tagging_info)

        p = Process(target=Videoprocessor.process, args=(VP,))
        p.start()
        return jsonify({'Response': True})


if __name__ == '__main__':
    app.run(use_debugger=True, use_reloader=True)
