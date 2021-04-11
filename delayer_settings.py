STREAM_DESTINATION = 'rtmp://127.0.0.1:1337/live'
DELAY = 120     # Seconds
SINGLE = False  # Set to true to just delay a single stream and exit, no reconnecting/backup-streams
BACKUPSTREAM_SHORT = '' # Show while intermission
BACKUPSTREAM_LONG = ''  # Show while longer downtime
FFMPEG_EXECUTABLE = "ffmpeg"   # Use avconv if you need
FFMPEG_EXTRA_OPTS = []  # Add extra options if necessary
