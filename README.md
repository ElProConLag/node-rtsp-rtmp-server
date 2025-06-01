### Repository Download
```bash
git clone https://github.com/ElProConLag/node-rtsp-rtmp-server.git
cd node-rtsp-rtmp-server
```
### Network Create (optional)
```bash
docker network create rtmpnet
```
### Server Deploy
```bash
make build && make console
```
### Network Capture
```bash
sudo timeout 30 tcpdump -i any -w tcpdump_capture.pcap
```
### Client One Deploy
```bash
docker build -f Dockerfile.cliente1 -t ffmpeg-client1 .
docker run -d --name ffmpeg-client1 --add-host host.docker.internal:host-gateway ffmpeg-client1
```
### Client Two Deploy
```bash
docker build -f Dockerfile.cliente2 -t ffmpeg-client2 .
docker run -d --name ffmpeg-client2 --add-host host.docker.internal:host-gateway ffmpeg-client2
```