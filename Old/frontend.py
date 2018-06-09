from flask import Flask
from flask import request
import json
app = Flask(__name__)


@app.route('/settings/<string:name>')
def settingsdetails(name):
    if name in ConfigManager.settings:
        return json.dumps(ConfigManager.settings[name]), 200, {'Content-Type': 'application/json'}
    else:
        return f'No such settings {name}, available settings are TOTO', 201

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'GET':
        return json.dumps(list(ConfigManager.settings.keys())), 200, {'Content-Type': 'application/json'}
    if request.method == 'POST':
        pass


if __name__ == '__main__':
    print('yeah')