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
```bash
make build && make console
```
You may also want to use just `make run` to run the container as a daemon.  If you fiddle with the ports, you'll need to update the values in the Makefile as well to expose the desired ports to your system.

### Serving MP4 files as recorded streams

MP4 files in `file` directory will be accessible at either:

- rtsp://localhost:80/file/FILENAME
- rtmp://localhost/file/mp4:FILENAME

For example, file/video.mp4 is available at rtmp://localhost/file/mp4:video.mp4

### Publishing live streams

```bash
docker build -f Dockerfile.cliente1 -t ffmpeg-client1 .
docker run -d --name ffmpeg-client1 --add-host host.docker.internal:host-gateway ffmpeg-client1
```

### Accessing the live stream

```bash
docker build -f Dockerfile.cliente2 -t ffmpeg-client2 .
docker run -d --name ffmpeg-client2 --add-host host.docker.internal:host-gateway ffmpeg-client2
```

### Creating network for Docker containers

```bash
docker network create rtmpnet
docker run --rm --network rtmpnet NOMBRE_CONTENEDOR NOMBRE_IMAGEN
```