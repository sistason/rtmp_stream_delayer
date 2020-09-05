#!/usr/bin/env python3
    iostname 195.192.129.164

import subprocess
import os, sys, time
import logging


if sys.version_info[0] == 2:
    print("You try to run the script with Python 2, but this is written in Python3!")
    print("Try to specify the correct version by using `sudo python3 rtmp_stream_delayer.py ...`, for example.")
    sys.exit(1)


logger = logging.getLogger(__name__)


class StreamDelayer:
    def __init__(self, stream_directory, stream_destination, backupstream_short, backupstream_long,
                 delay=300, single=False, ffmpeg_exe="ffmpeg"):
        self.stream_directory = stream_directory

        self.stream_destination = stream_destination
        self.backupstream_short = backupstream_short
        self.backupstream_long = backupstream_long
        self.delay = delay
        self.single = single
        self.ffmpeg_exe = ffmpeg_exe

        self.stream = self._wait_for_stream()

    def _wait_for_stream(self):
        streams = self._get_streams_in_directory()
        while not streams:
            time.sleep(0.5)
            streams = self._get_streams_in_directory()

        logging.debug("Found Streams: {}".format(', '.join(streams)))

        return self._keep_only_latest(streams)

    def _get_streams_in_directory(self):
        return [os.path.join(self.stream_directory, _i)
                for _i in os.listdir(self.stream_directory) if _i.endswith('.flv')]

    def _keep_only_latest(self, streams):
        """ keep the newest stream, if multiple streams are present """

        if len(streams) <= 1:
            return streams[0]

        nearest = max(streams, key=self.get_date_from_file)
        streams.remove(nearest)

        for stream in streams:
            try:
                os.remove(os.path.join(self.stream_directory, stream))
            except:
                pass

        return os.path.join(self.stream_directory, nearest)

    def _get_oldest_stream(self):
        streams = self._get_streams_in_directory()
        if streams:
            return os.path.join(self.stream_directory, min(streams, key=self.get_date_from_file))

    def delay_stream(self):
        """ Delay a stream.

        Delay the first stream, when it ends check for new files"""
        stream_date = self.get_date_from_file(self.stream)
        logging.debug('Delaying stream for {:.0f} seconds...'.format(stream_date + DELAY - time.time()))
        while time.time() < stream_date + DELAY:
            time.sleep(0.5)

        self.publish_stream()
        if SINGLE:
            # finish if this is just a one-shot
            return

        self.stream = self._get_oldest_stream()
        while self.stream:
            # If there are more files, it means the stream was interrupted by error, so show wait-stream and continue
            stream_date = self.get_date_from_file(self.stream)

            wait_time = (stream_date + DELAY) - time.time()
            self.publish_wait(wait_time)

            self.publish_stream()

            self.stream = self._get_oldest_stream()

    def publish_stream(self):
        """ Publish the current stream.

        Returns True on ok, returns False if crashed"""

        logger.debug('Publishing stream {}'.format(self.stream))
        return_code = True
        try:
            subprocess.check_output(
                [self.ffmpeg_exe, '-re', '-i', self.stream, '-codec', 'copy', '-f', 'flv', self.stream_destination])
        except Exception as e:
            logger.error('Publish stream threw exception {}'.format(e))
            return_code = False
        finally:
            try:
                os.remove(self.stream)
            except:
                pass
        return return_code

    def publish_wait(self, wait_time):
        """ Publish waiting/backup streams, when main stream is down.

        Depending on the waiting time, a short outage or 'Problems' or whatever"""
        if wait_time < 10:
            if not self.backupstream_short:
                logger.debug('Normally publising a short waitstream, but was not configured...')
                time.sleep(wait_time)
            else:
                logger.debug('Publishing waitstream short...')
                subprocess.check_output([self.ffmpeg_exe, '-re',
                                         '-i', self.backupstream_short, '-codec', 'copy', '-f', 'flv',
                                         self.stream_destination])
        else:
            if not self.backupstream_long:
                logger.debug('Normally publising a long waitstream, but was not configured...')
                time.sleep(wait_time)
            else:
                logger.debug('Publishing waitstream long...')
                subprocess.check_output([self.ffmpeg_exe, '-re',
                                         '-i', self.backupstream_long, '-codec', 'copy', '-f', 'flv',
                                         self.stream_destination])

    @staticmethod
    def get_date_from_file(file_):
        """ nginx saves streams as: test-%s.flv """
        try:
            return int(file_.split('-')[-1].split('.')[0])
        except ValueError:
            return 0


if __name__ == '__main__':
    def parse_args():
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument('-v', '--verbose', action="store_true")
        parser.add_argument('-q', '--quiet', action="store_true")
        parser.add_argument('-w', '--delay', type=int, default=None)
        parser.add_argument('-s', '--single', action="store_true", default=None)
        parser.add_argument('-d', '--destination', type=str, default=None)
        parser.add_argument('stream_dir')

        _args = parser.parse_args()
        return _args

    def set_loglevel(args):
        log_level = logging.INFO
        if args.verbose:
            log_level -= 10
        if args.quiet:
            log_level += 20
        logging.basicConfig(level=log_level)

    def check_running(PID_FILE):
        """ Only one stream at a time """
        try:
            with open(PID_FILE) as f:
                pid = f.read().strip()
        except FileNotFoundError:
            pid = ""

        if pid.isnumeric():
            """ Check for the existence of a unix pid by sending signal 0 """
            try:
                os.kill(int(pid), 0)
            except OSError:
                pass
            else:
                logger.error('stream_delayer already running (PID-file at {} says it is pid={}!'.format(PID_FILE, pid))
                return True

        with open(PID_FILE, 'w') as f:
            f.write(str(os.getppid()))

    args = parse_args()
    set_loglevel(args)

    PID_FILE = os.path.join(args.stream_dir, "stream_delayer_pid")
    if check_running(PID_FILE):
        sys.exit(0)

    try:
        while True:
            from delayer_settings import BACKUPSTREAM_SHORT, BACKUPSTREAM_LONG, \
                STREAM_DESTINATION, DELAY, SINGLE, FFMPEG_EXECUTABLE
            destination = args.destination if args.destination is not None  else STREAM_DESTINATION
            delay = args.delay if args.delay is not None else DELAY
            single = args.single if args.single is not None else SINGLE

            streamer = StreamDelayer(args.stream_dir, destination, BACKUPSTREAM_SHORT, BACKUPSTREAM_LONG,
                                     delay=delay, single=single, ffmpeg_exe=FFMPEG_EXECUTABLE)
            streamer.delay_stream()

    except KeyboardInterrupt:
        pass
    finally:
        os.remove(PID_FILE)
