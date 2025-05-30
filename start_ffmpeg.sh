#!/bin/sh
ffmpeg -stream_loop -1 -re -i file/bbb_sunflower_1080p_30fps_normal.mp4 -c:v libx264 -preset fast -c:a aac -ac 2 -ab 128k -ar 44100 -f flv rtmp://host.docker.internal:1935/live/bigbuckbunny &
tail -f /dev/null
