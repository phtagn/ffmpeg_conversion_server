#!/usr/bin/env python

import locale
import logging
import os
import os.path
import re
import signal
from subprocess import Popen, PIPE
from typing import Union
from converter.parsers import FFprobeParser
import sys
from converter.streamoptions import Language

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
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
        error = self.details if self.details else self.message
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
            path = os.environ.get_parser('PATH', os.defpath)
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

        self.encoders = []
        self.decoders = []

        self._getcapabilities()

    def _getcapabilities(self):

        p = self._spawn([self.ffmpeg_path, '-v', 0, '-encoders'])
        stdout, _ = p.communicate()
        stdout = stdout.decode(console_encoding, errors='ignore')

        start = False
        for line in stdout.split('\n'):
            theline = line.strip()
            if theline == '------':
                start = True
                continue
            if start:
                try:
                    codectype, codecname, *_ = re.split(r' ', theline)
                except ValueError:
                    pass
                if codectype[0] in ['V', 'A', 'S']:
                    self.encoders.append(codecname)

        p = self._spawn([self.ffmpeg_path, '-v', 0, '-decoders'])
        stdout, _ = p.communicate()
        stdout = stdout.decode(console_encoding, errors='ignore')

        start = False
        for line in stdout.split('\n'):
            theline = line.strip()
            if theline == '------':
                start = True
                continue
            if start:
                try:
                    codectype, codecname, *_ = re.split(r' ', theline)
                except ValueError:
                    pass
                if codectype[0] in ['V', 'A', 'S']:
                    self.decoders.append(codecname)

    @staticmethod
    def _spawn(cmds):
        clean_cmds = []
        try:
            for cmd in cmds:
                clean_cmds.append(str(cmd))
            cmds = clean_cmds
        except:
            log.exception("There was an error making all command line parameters a string")
        log.debug('Spawning ffmpeg with command: ' + ' '.join(cmds))
        return Popen(cmds, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE,
                     close_fds=(os.name != 'nt'), startupinfo=None)

    def probe(self, fname, posters_as_video=True) -> FFprobeParser:
        """
        Examine the media file and determine its format and media streams.
        Returns the MediaInfo object, or None if the specified file is
        not a valid media file.

        >>> parsers = FFMpeg().probe('test1.ogg')
        >>> parsers.format
        'ogg'
        >>> parsers.duration
        33.00
        >>> parsers.video.codec
        'theora'
        >>> parsers.video.width
        720
        >>> parsers.video.height
        400
        >>> parsers.audio.codec
        'vorbis'
        >>> parsers.audio.channels
        2
        :param posters_as_video: Take poster images (mainly for audio files) as
            A video stream, defaults to True
        """

        if not os.path.exists(fname):
            return None

        p = self._spawn([self.ffprobe_path,
                         '-show_format', '-show_streams', '-hide_banner', '-print_format', 'json', fname])
        stdout_data, _ = p.communicate()
        stdout_data = stdout_data.decode(console_encoding, errors='ignore')
        parser = FFprobeParser(stdout_data)

        return parser

    def generate_commands(self, source_container, target_container, mapping, encoder_factory, timeout=10, preopts=None,
                          postopts=None):
        """

        :param source_container:
        :type source_container: converter.containers.Container
        :param target_container:
        :type target_container: converter.containers.Container
        :param mapping:
        :type mapping: list
        :param encoder_factory:
        :type encoder_factory: converter.encoders.EncoderFactory
        :param timeout:
        :param preopts:
        :param postopts:
        :return: list
        """
        from helpers.helpers import breakdown
        if os.name == 'nt':
            timeout = 0

        path_elements = breakdown(target_container.file_path)

        cmds = [self.ffmpeg_path,
                '-i',
                source_container.file_path]
        if preopts:
            cmds.extend(preopts)

        for source_index, target_index in mapping:
            source_stream = source_container.streams[source_index]
            target_stream = target_container.streams[target_index]  # type: converter.streams.Stream

            encoder = encoder_factory.get_encoder(source_stream, target_stream)

            if 'copy' in encoder.codec_name:
                encoder.add_option(*target_stream.options.metadata_options())
                if target_stream.options.has_option(Language):
                    encoder.add_option(target_stream.options.get_unique_option(Language))
            else:
                encoder.add_option(*target_stream.options)

            cmds.extend(encoder.parse(target_container.relative_stream_number(target_stream)))

        if postopts:
            cmds.extend(postopts)

        cmds.extend(['-y', target_container.file_path])

        log.debug(' '.join(cmds))
        sys.exit(0)
        p = Popen(cmds, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE,
                  close_fds=(os.name != 'nt'), startupinfo=None)
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
                    print(timecode)

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

        return outfile

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
