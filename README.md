# rtmp_stream_delayer

Uses ffmpeg and nginx to delay (buffer) an incoming rtmp-stream for an amount of time.

In the (rare) case that you want to delay a rtmp-stream instead of minimise the delay, this python-script plus the nginx-config will rudimentarily do the job.

The most common scenario requiring a delayed stream is a game stream. 
Since you do not want your opponents to know what you see, to prevent them from cheating, you stream with a delay, usually between 30sec and 5mins. 
Most streaming software has already implemented such a feature, for example OBS and xsplit,
BUT the stream is buffered in the client, which is very near the point of a failure, for example PC crashes, network outages or software bugs. 
In that case, the buffered content can be lost, which leads to the stream being down for $buffered_time, $time_to_fix and $delay_until_start_streaming. 
When delaying the stream at a server (with hopefully better stability), the downtime can be reduced to $time_to_fix, while also displaying a backup-stream while the main-stream is down.

The setup is based on nginx, although other rtmp-streaming(/multiplexing)-software could also work, if you configure it right.

## Alternative

@invisan also coded something like this, but more recently. Check out their work if you have problems with this one or need the features they provide: [https://github.com/invisan/rtmpdelayer](https://github.com/invisan/rtmpdelayer)

# Installation

- Python
- nginx + the [nginx-rtmp-module](https://github.com/arut/nginx-rtmp-module)
- Merge the nginx.conf here with your local nginx.conf

# Usage

- nginx.conf:
  - Setup your push-targets and specify the location of the recording-location
- delayer_settings.py
  - Specify the required delay
  - Specify the stream destination (the server location in your nginx conf, or the destination directly)
  - Optional:
    - Specify the backup streams OR
    - Set SINGLE=True to exit after delaying one stream
    - set FFMPEG_EXECUTABLE to avconv or a custom path

1. Start the python-script somewhere with the stream_directory as argument.
2. Nginx gets the stream and records it to the stream_directory. 
3. The python-script monitors the stream_directory, delays incoming streams and publishes them again.

You can run one stream-delayer per stream_directory.

# Caveats

- Backup-Streams work, but the distinction between the stream legitimately ending and it crashing is not known. 
We assume: no new file after the stream ended => end.
Because of that, the downtime of the client cannot be longer than $DELAY
- There will be artefacts/gaps even when using backup-streams, 
as downtimes/buffers are at various places in nearly all video processing pipelines (at twitch for example) 


