### RTSP, RTMP, and HTTP server in Node.js

- Supports RTSP, RTMP/RTMPE/RTMPT/RTMPTE, and HTTP.
- Supports only H.264 video and AAC audio (AAC-LC, HE-AAC v1/v2).

### Installation

```bash
git clone https://github.com/ElProConLag/node-rtsp-rtmp-server.git
cd node-rtsp-rtmp-server
```

Also, install [CoffeeScript](https://coffeescript.org/) 1.x or 2.x.

### Configuration

Edit `config.coffee`.

### Starting the server

    $ cd node-rtsp-rtmp-server
    $ sudo coffee server.coffee

or use Node.js directly:

    $ cd node-rtsp-rtmp-server
    $ coffee -c *.coffee
    $ sudo node server.js

If both `serverPort` and `rtmpServerPort` are >= 1024 in `config.coffee`, `sudo` is not needed.

### Docker Deploy Method

If you would prefer building and executing this code in a docker container, you can do so by first building the container and then running it.

    $  make build
    $  make console

You may also want to use just `make run` to run the container as a daemon.  If you fiddle with the ports, you'll need to update the values in the Makefile as well to expose the desired ports to your system.

### Serving MP4 files as recorded streams

MP4 files in `file` directory will be accessible at either:

- rtsp://localhost:80/file/FILENAME
- rtmp://localhost/file/mp4:FILENAME

For example, file/video.mp4 is available at rtmp://localhost/file/mp4:video.mp4

### Publishing live streams

#### From FFmpeg

```bash
ffmpeg -stream_loop -1 -re -i file/bbb_sunflower_1080p_30fps_normal.mp4 -c:v libx264 -preset fast -c:a aac -ac 2 -ab 128k -ar 44100 -f flv rtmp://localhost:1935/live/bigbuckbunny
```

#### From RTSP client

You can publish streams from RTSP client such as FFmpeg.

    $ ffmpeg -re -i input.mp4 -c:v libx264 -preset fast -c:a libfdk_aac -ab 128k -ar 44100 -f rtsp rtsp://localhost:80/live/STREAM_NAME

Or you can publish it over TCP instead of UDP, by specifying `-rtsp_transport tcp` option. TCP is favorable if you publish large data from FFmpeg.

    $ ffmpeg -re -i input.mp4 -c:v libx264 -preset fast -c:a libfdk_aac -ab 128k -ar 44100 -f rtsp -rtsp_transport tcp rtsp://localhost:80/live/STREAM_NAME

### Accessing the live stream

```bash
ffmpeg -y -i rtmp://localhost:1935/live/bigbuckbunny -c copy grabacion.flv
```


### Creating network for Docker containers

```bash
docker network create rtmpnet
docker run --rm --network rtmpnet NOMBRE_CONTENEDOR NOMBRE_IMAGEN
```