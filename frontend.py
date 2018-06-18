import configuration
import os
from flask import Flask, jsonify, abort
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


