# coding=utf-8
import locale

console_encoding = locale.getdefaultlocale()[1] or 'UTF-8'

import converter.ffmpeg
import re

prog = converter.ffmpeg.FFMpeg('/usr/local/bin/ffmpeg', '/usr/local/bin/ffprobe')
p = prog._spawn(['/usr/local/bin/ffmpeg', '-v', 0, '-codecs'])
stdout, _ = p.communicate()
stdout = stdout.decode(console_encoding, errors='ignore')
line = str
start = False
videocodecs = []
video = re.compile('^V(?:\S+ )(\S+)')
encoders = {'video': [],
            'audio': [],
            'subtitle': []}

decoders = {'video': [],
            'audio': [],
            'subtitle': []}


def sortcodec(letter: str):
    if letter == 'V':
        return 'video'
    elif letter == 'A':
        return 'audio'
    elif letter == 'S':
        return 'subtitle'
    else:
        return None


regexp = re.compile('([?D?E]+)\s([a-zA-Z,_0-9]+)')

p = prog._spawn(['/usr/local/bin/ffmpeg', '-formats'])
stdout, _ = p.communicate()
stdout = stdout.decode(console_encoding, errors='ignore')

for line in stdout.split('\n'):
    theline = line.strip()
    if theline == '--':
        start = True
        continue
    if start:
        if re.match(regexp, theline):
            m = re.search(regexp, theline)
            print(m.group(0))

for line in stdout.split('\n'):
    theline = line.strip()
    if theline == '-------':
        start = True
        continue
    if start:
        try:
            codectype, codecname, *_ = re.split(r' ', theline)
        except ValueError:
            pass
        if codectype[1] == 'E':
            if sortcodec(codectype[2]):
                encoders[sortcodec(codectype[2])].append(codecname)
        if codectype[0] == 'D':
            if sortcodec(codectype[2]):
                decoders[sortcodec(codectype[2])].append(codecname)
