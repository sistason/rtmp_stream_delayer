#!/usr/bin/env python
#

import subprocess
import os, sys

import time

from delayer_settings import BACKUPSTREAM_SHORT, BACKUPSTREAM_LONG, STREAM_DIR, STREAM_DESTINATION, DELAY

def check_running():
    """ Only one stream at a time """

    all_procs = subprocess.check_output(['ps', 'aux'])
    if all_procs.count(" python rtmp_stream_delayer.py") > 1:
        return True

def cleanup(streams):
    """ keep the newest stream, if multiple streams are present """

    current_date = time.time()
    nearest = min(streams, key=lambda f: abs(current_date - get_date_from_file(f)))

    for stream in streams:
        if stream == nearest:
            continue
        try:
            os.remove(os.path.join(STREAM_DIR, stream))
        except:
            pass
    return [os.path.join(STREAM_DIR, nearest)]

def publish_stream(filename):
    """ Publish the current stream. 
    
    Returns True on ok, returns False if crashed and needs reconnects """

    print 'Publishing stream', filename
    ret = False
    try:
        #TODO: When is the stream finished or when is it crashed?
        subprocess.check_output('avconv -re -i {0} -codec copy -f flv {1}'.format(filename, STREAM_DESTINATION).split())
        ret = False
    except:
        ret = False
    try:
        os.remove(filename)
    except:
        pass
    return ret

def publish_wait(wait_time):
    """ Publish waiting/backup streams, when main stream is down.

    Depending on the waiting time, a short outage or 'Problems' or whatever"""
    if wait_time < 10:
        problems_short = BACKUPSTREAM_SHORT
        subprocess.check_output('avconv -re -i {0} -codec copy -f flv {1}'.format(problems_short, STREAM_DESTINATION).split())
    else:
        problems_big = BACKUPSTREAM_LONG
        subprocess.check_output('avconv -re -i {0} -codec copy -f flv {1}'.format(problems_big, STREAM_DESTINATION).split())

def get_date_from_file(file_):
    """ nginx saves streams as: test-%s.flv """
    try:
        return int(file_.split('-')[-1].split('.')[0])
    except ValueError:
        return 0

if __name__ == '__main__':
    # One to rule them all.
    if check_running():
        sys.exit(0)

    stream = [_i for _i in os.listdir(STREAM_DIR) if _i.endswith('.flv')]
    while not stream:
        time.sleep(0.5)
        stream = [_i for _i in os.listdir(STREAM_DIR) if _i.endswith('.flv')]

    if len(stream) > 1:
        stream = cleanup(stream)

    first = True
    while stream:
        stream = stream[0]
        stream_date = get_date_from_file(stream)

        if first:
            # On first run, just delay the begin of the stream
            print (stream_date+DELAY) - time.time()
            while time.time() < stream_date+DELAY:
                time.sleep(0.5)
        else:
            # On next runs, which are reconnects, show offline/backup-stream
            wait_time = (stream_date+DELAY) - time.time()
            publish_wait(wait_time)

        if publish_stream(stream):
            # If the stream is just finished, our work here is done
            break
        
        stream = sorted([_i for _i in os.listdir(STREAM_DIR) if _i.endswith('.flv')])
        first = False
