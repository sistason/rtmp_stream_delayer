# rtmp_stream_delayer
Uses ffmpeg and nginx to delay (buffer) an incoming rtmp-stream for an amount of time.

In the (rare) case that you want to delay a rtmp-stream instead of minimise the delay, this python-script plus the nginx-config will rudimentarily do the job.

The most common scenario requiring a delayed stream is a game stream. Since you do not want your opponents to know what you see, to prevent them from cheating, you stream with a delay, usually between 30sec and 5mins. 
Most streaming software has already implemented such a feature, for example OBS and xsplit, BUT the stream is buffered in the client, which is very near the point of a failure, for example PC crashes, network outages or software bugs. In that case, the buffered content can be lost, which leads to the stream being down for $buffered_time, $time_to_fix and $delay_until_start_streaming. When delaying the stream at a server (with hopefully better stability), the downtime can be reduced to $time_to_fix, while also displaying a backup-stream while the main-stream is down.

The setup is based on nginx, although other rtmp-streaming(/multiplexing)-software will also work, if you configure it right.
Nginx takes the stream, records it to disk and starts the python-script, which waits until the stream is delayed enough and publishes it locally back to nginx or directly to the intended target. This is done by using ffmpeg and the copy-codec + native bitrate, so not much performance is required.

Installation
===========
* Python 2 (2.7, but should work maybe down to 2.5)
* nginx + the [nginx-rtmp-module][https://github.com/arut/nginx-rtmp-module]
* Merge the nginx.conf here with your local nginx.conf

Usage
=====
* nginx.conf:
	Setup your push-targets and specify the location of the python-script/recording-location
* delayer_settings.py
	Specify your recording-location
	Specify the required delay
	Specify the stream destination (nginx, twitch, etc.)
	Specify the backup streams

Current State
=============
* It works to delay the stream, but it cannot distinguish between the stream legitimately ending and it crashing. Because of that, the downtime of the client cannot be longer than $DELAY, after which it is assumed the streaming ended for good (no new file after the stream ended => end)
* 5-10s delay to push the stream further (probably induced by twitch). Leads to a downtime of ~5s before starting the backup-stream (ugly)
* BETA. Not that much code, but there could be bugs, especially when trying things aside the road.


