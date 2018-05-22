#!/usr/bin/env python

import locale
import logging
import os
import os.path
import re
import signal
from subprocess import Popen, PIPE
from converter.streaminfo import MediaStreamInfo, MediaInfo, Parser
import languagecode

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
console_encoding = locale.getdefaultlocale()[1] or 'UTF-8'


class FFMpegError(Exception):
    pass


class FFMpegConvertError(Exception):
    def __init__(self, message, cmd, output, details=None, pid=0):
        """
        @param    message: Error message.
        @type     message: C{str}

        @param    cmd: Full command string used to spawn ffmpeg.
        @type     cmd: C{str}

        @param    output: Full stdout output from the ffmpeg command.
        @type     output: C{str}

        @param    details: Optional error details.
        @type     details: C{str}
        """
        super(FFMpegConvertError, self).__init__(message)

        self.cmd = cmd
        self.output = output
        self.details = details
        self.pid = pid

    def __repr__(self):
        error = self.details if self.details else self.\
            message
        return ('<FFMpegConvertError error="%s", pid=%s, cmd="%s">' %
                (error, self.pid, self.cmd))

    def __str__(self):
        return self.__repr__()


class FFMpeg(object):
    """
    FFMPeg wrapper object, takes care of calling the ffmpeg binaries,
    passing options and parsing the output.

    >>> f = FFMpeg()
    """
    DEFAULT_JPEG_QUALITY = 4

    def __init__(self, ffmpeg_path=None, ffprobe_path=None):
        """
        Initialize a new FFMpeg wrapper object. Optional parameters specify
        the paths to ffmpeg and ffprobe utilities.
        """

        def which(name):
            path = os.environ.get('PATH', os.defpath)
            for d in path.split(':'):
                fpath = os.path.join(d, name)
                if os.path.exists(fpath) and os.access(fpath, os.X_OK):
                    return fpath
            return None

        if ffmpeg_path is None:
            ffmpeg_path = 'ffmpeg'

        if ffprobe_path is None:
            ffprobe_path = 'ffprobe'

        if '/' not in ffmpeg_path:
            ffmpeg_path = which(ffmpeg_path) or ffmpeg_path
        if '/' not in ffprobe_path:
            ffprobe_path = which(ffprobe_path) or ffprobe_path

        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path

        if not os.path.exists(self.ffmpeg_path):
            raise FFMpegError("ffmpeg binary not found: " + self.ffmpeg_path)

        if not os.path.exists(self.ffprobe_path):
            raise FFMpegError("ffprobe binary not found: " + self.ffprobe_path)

        self.hwaccels = []

        self.encoders = {'video': [],
                         'audio': [],
                         'subtitle': []}
        self.decoders = {'video': [],
                         'audio': [],
                         'subtitle': []}

        self._getcapabilities()

    def _getcapabilities(self):

        def sortcodec(letter: str):
            if letter == 'V':
                return 'video'
            elif letter == 'A':
                return 'audio'
            elif letter == 'S':
                return 'subtitle'
            else:
                return None

        p = self._spawn([self.ffmpeg_path, '-v', 0, '-codecs'])
        stdout, _ = p.communicate()
        stdout = stdout.decode(console_encoding, errors='ignore')

        start = False
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
                        self.encoders[sortcodec(codectype[2])].append(codecname)
                if codectype[0] == 'D':
                    if sortcodec(codectype[2]):
                        self.decoders[sortcodec(codectype[2])].append(codecname)

    @staticmethod
    def _spawn(cmds):
        clean_cmds = []
        try:
            for cmd in cmds:
                clean_cmds.append(str(cmd))
            cmds = clean_cmds
        except:
            logger.exception("There was an error making all command line parameters a string")
        logger.debug('Spawning ffmpeg with command: ' + ' '.join(cmds))
        print(' '.join(cmds))
        return Popen(cmds, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE,
                     close_fds=(os.name != 'nt'), startupinfo=None)

    def probe(self, fname, posters_as_video=True):
        """
        Examine the media file and determine its format and media streams.
        Returns the MediaInfo object, or None if the specified file is
        not a valid media file.

        >>> info = FFMpeg().probe('test1.ogg')
        >>> info.format
        'ogg'
        >>> info.duration
        33.00
        >>> info.video.codec
        'theora'
        >>> info.video.width
        720
        >>> info.video.height
        400
        >>> info.audio.codec
        'vorbis'
        >>> info.audio.channels
        2
        :param posters_as_video: Take poster images (mainly for audio files) as
            A video stream, defaults to True
        """

        if not os.path.exists(fname):
            return None

        p = self._spawn([self.ffprobe_path,
                         '-show_format', '-show_streams', fname])
        stdout_data, _ = p.communicate()
        stdout_data = stdout_data.decode(console_encoding, errors='ignore')
        media = FFprobeParser(stdout_data).parse()

        #if not info.format.format and len(info.streams) == 0:
        #    return None

        return media

    def convert(self, infile, outfile, opts, timeout=10, preopts=None, postopts=None):
        """
        Convert the source media (infile) according to specified options
        (a list of ffmpeg switches as strings) and save it to outfile.

        Convert returns a generator that needs to be iterated to drive the
        conversion process. The generator will periodically yield timecode
        of currently processed part of the file (ie. at which second in the
        content is the conversion process currently).

        The optional timeout argument specifies how long should the operation
        be blocked in case ffmpeg gets stuck and doesn't report back. See
        the documentation in Converter.convert() for more details about this
        option.

        >>> conv = FFMpeg().convert('test.ogg', '/tmp/output.mp3',
        ...    ['-acodec libmp3lame', '-vn'])
        >>> for timecode in conv:
        ...    pass # can be used to inform the user about conversion progress

        """
        if os.name == 'nt':
            timeout = 0

        if not os.path.exists(infile):
            raise FFMpegError("Input file doesn't exist: " + infile)

        cmds = [self.ffmpeg_path]
        if preopts:
            cmds.extend(preopts)
        cmds.extend(['-i', infile])

        # Move additional inputs to the front of the line
        for ind, command in enumerate(opts):
            if command == '-i':
                cmds.extend(['-i', opts[ind + 1]])
                del opts[ind]
                del opts[ind]

        cmds.extend(opts)
        if postopts:
            cmds.extend(postopts)
        cmds.extend(['-y', outfile])

        if timeout:
            def on_sigalrm(*_):
                signal.signal(signal.SIGALRM, signal.SIG_DFL)
                raise Exception('timed out while waiting for ffmpeg')

            signal.signal(signal.SIGALRM, on_sigalrm)

        try:
            p = self._spawn(cmds)
        except OSError:
            raise FFMpegError('Error while calling ffmpeg binary')

        yielded = False
        buf = ''
        total_output = ''
        pat = re.compile(r'time=([0-9.:]+) ')
        while True:
            if timeout:
                signal.alarm(timeout)

            ret = p.stderr.read(10)

            if timeout:
                signal.alarm(0)

            if not ret:
                # For small or very fast jobs, ffmpeg may never output a '\r'.  When EOF is reached, yield if we haven't yet.
                if not yielded:
                    yielded = True
                    yield 10
                break

            try:
                ret = ret.decode(console_encoding)
            except UnicodeDecodeError:
                try:
                    ret = ret.decode(console_encoding, errors="ignore")
                except:
                    pass

            total_output += ret
            buf += ret
            if '\r' in buf:
                line, buf = buf.split('\r', 1)

                tmp = pat.findall(line)
                if len(tmp) == 1:
                    timespec = tmp[0]
                    if ':' in timespec:
                        timecode = 0
                        for part in timespec.split(':'):
                            timecode = 60 * timecode + float(part)
                    else:
                        timecode = float(tmp[0])
                    yielded = True
                    yield timecode

        if timeout:
            signal.signal(signal.SIGALRM, signal.SIG_DFL)

        p.communicate()  # wait for process to exit

        if total_output == '':
            raise FFMpegError('Error while calling ffmpeg binary')

        cmd = ' '.join(cmds)
        if '\n' in total_output:
            line = total_output.split('\n')[-2]

            if line.startswith('Received signal'):
                # Received signal 15: terminating.
                raise FFMpegConvertError(line.split(':')[0], cmd, total_output, pid=p.pid)
            if line.startswith(infile + ': '):
                err = line[len(infile) + 2:]
                raise FFMpegConvertError('Encoding error', cmd, total_output,
                                         err, pid=p.pid)
            if line.startswith('Error while '):
                raise FFMpegConvertError('Encoding error', cmd, total_output,
                                         line, pid=p.pid)
            if not yielded:
                raise FFMpegConvertError('Unknown ffmpeg error', cmd,
                                         total_output, line, pid=p.pid)
        if p.returncode != 0:
            raise FFMpegConvertError('Exited with code %d' % p.returncode, cmd,
                                     total_output, pid=p.pid)

    def thumbnail(self, fname, time, outfile, size=None, quality=DEFAULT_JPEG_QUALITY):
        """
        Create a thumbnal of media file, and store it to outfile
        @param time: time point (in seconds) (float or int)
        @param size: Size, if specified, is WxH of the desired thumbnail.
            If not specified, the video resolution is used.
        @param quality: quality of jpeg file in range 2(best)-31(worst)
            recommended range: 2-6

        >>> FFMpeg().thumbnail('test1.ogg', 5, '/tmp/shot.png', '320x240')
        """
        return self.thumbnails(fname, [(time, outfile, size, quality)])

    def thumbnails(self, fname, option_list):
        """
        Create one or more thumbnails of video.
        @param option_list: a list of tuples like:
            (time, outfile, size=None, quality=DEFAULT_JPEG_QUALITY)
            see documentation of `converter.FFMpeg.thumbnail()` for details.

        >>> FFMpeg().thumbnails('test1.ogg', [(5, '/tmp/shot.png', '320x240'),
        >>>                                   (10, '/tmp/shot2.png', None, 5)])
        """
        if not os.path.exists(fname):
            raise IOError('No such file: ' + fname)

        cmds = [self.ffmpeg_path, '-i', fname, '-y', '-an']
        for thumb in option_list:
            if len(thumb) > 2 and thumb[2]:
                cmds.extend(['-s', str(thumb[2])])

            cmds.extend([
                '-f', 'image2', '-vframes', '1',
                '-ss', str(thumb[0]), thumb[1],
                '-q:v', str(FFMpeg.DEFAULT_JPEG_QUALITY if len(thumb) < 4 else str(thumb[3])),
            ])

        p = self._spawn(cmds)
        _, stderr_data = p.communicate()
        if stderr_data == '':
            raise FFMpegError('Error while calling ffmpeg binary')
        stderr_data.decode(console_encoding)
        if any(not os.path.exists(option[1]) for option in option_list):
            raise FFMpegError('Error creating thumbnail: %s' % stderr_data)


class FFprobeParser(Parser):
    """
    Parse raw ffprobe output (key=value).
    Returns a the appropriate MediaStreamInfo object
    """
    def __init__(self, output):
        self.output = output
        super(FFprobeParser, self).__init__()

    def parse(self):
        """
        Parse raw ffprobe output.

        """
        media = MediaInfo()
        in_format = False
        current_stream = None

        for line in self.output.split('\n'):
            line = line.strip()
            if line == '':
                continue
            elif line == '[STREAM]':
                current_stream = MediaStreamInfo()
            elif line == '[/STREAM]':
                if current_stream.type:
                    media.add_stream(current_stream.type, current_stream)
                current_stream = None

            elif line == '[FORMAT]':
                in_format = True
            elif line == '[/FORMAT]':
                in_format = False

            elif '=' in line:
                k, v = line.split('=', 1)
                k = k.strip()
                v = v.strip()
                if current_stream:
                    stream_key, stream_value = self._parse_stream(k, v)
                    if stream_key:
                        if hasattr(current_stream, stream_key):
                            setattr(current_stream, stream_key, stream_value)
                elif in_format:
                    format_key, format_value = self._parse_format(k, v)
                    if format_key:
                        setattr(media.format, format_key, format_value)

        return media

    def _parse_stream(self, key, val):

        if key == 'index':
            return 'index', self.parse_int(val)

        elif key == 'codec_type':
            return 'type', val.lower()

        elif key == 'codec_name':
            return 'codec',  val.lower()

        elif key == 'codec_long_name':
            return 'codec_desc', val.lower()

        elif key == 'duration':
            return 'duration', self.parse_float(val)

        elif key == 'bit_rate':
            return 'bitrate', self.parse_int(val, None)

        elif key == 'width':
            return 'width', self.parse_int(val)

        elif key == 'height':
            return 'height', self.parse_int(val)

        elif key == 'channels':
            return 'channels',  self.parse_int(val)

        elif key == 'sample_rate':
            return 'samplerate',  self.parse_float(val)

        elif key == 'profile':
            return 'profile', val.lower()

        elif key == 'has_b_frames':
            return 'bframes',  self.parse_int(val)

        elif key == 'level':
            return 'level', self.parse_float(val)

        elif key == 'pix_fmt':
            return 'pix_fmt', val.lower()

        elif key == 'DISPOSITION:forced':
            return 'disposition',  {'forced': self.parse_int(val)}

        elif key == 'DISPOSITION:default':
            return 'disposition', {'default': self.parse_int(val)}

        if key.startswith('TAG:'):
            key = key.split('TAG:')[1].lower()
            value = val.lower().strip()
            if key == 'language':
                try:
                    return 'metadata', {key: languagecode.validate(value)}
                except:
                    return 'metadata', {key: value}
            else:
                return 'metadata', {key: value}

        return None, None

#        if stream.type == 'audio':
#            if key == 'avg_frame_rate':
#                if '/' in val:
#                    n, d = val.split('/')
#                    n = self.parse_float(n)
#                    d = self.parse_float(d)
#                    if n > 0.0 and d > 0.0:
#                        video_fps = float(n) / float(d)
#                elif '.' in val:
#                    video_fps = self.parse_float(val)
#                    return 'fps', video_fps

#        if stream.type == 'video':
#            if key == 'r_frame_rate':
#                if '/' in val:
#                    n, d = val.split('/')
#                    n = self.parse_float(n)
#                    d = self.parse_float(d)
#                    if n > 0.0 and d > 0.0:
#                        stream.video_fps = float(n) / float(d)
#                elif '.' in val:
#                    stream.video_fps = self.parse_float(val)
#                    return 'fps', video_fps




    def _parse_format(self, key, val):
        """
        Parse raw ffprobe output (key=value).
        """
        if key == 'format_name':
            return 'format_name', val
        elif key == 'format_long_name':
            return 'fullname', val
        elif key == 'bit_rate':
            return 'bitrate', self.parse_float(val, None)
        elif key == 'duration':
            return 'duration', self.parse_float(val, None)
        elif key == 'size':
            return 'filesize', self.parse_float(val, None)

        return None, None

if __name__ == '__main__':
    ffmpeg = FFMpeg('/usr/local/bin/ffmpeg', '/usr/local/bin/ffprobe')
    mimi = ffmpeg.probe('/Users/jon/Downloads/Geostorm 2017 1080p FR EN X264 AC3-mHDgz.mkv')
    momo = ffmpeg.probe('/Users/jon/Downloads/Geostorm 2017 1080p FR EN X264 AC3-mHDgz.mkv')

    momo.videostreams[0].width += 1
    print(mimi.videostreams[0].should_transcode(momo.videostreams[0]))