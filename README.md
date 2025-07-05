# Node RTSP/RTMP Server

![RTMP Client-Server Interaction](image.png)


## Acerca del Proyecto

Este proyecto implementa un servidor de streaming RTMP y RTSP basado en Node.js. Utiliza contenedores Docker para facilitar el despliegue del servidor y de los clientes FFmpeg para la emisión y grabación de streams.

El diagrama anterior ilustra el flujo de comunicación estándar entre un cliente y un servidor RTMP.

## Construido Con

*   [Node.js](https://nodejs.org/)
*   [CoffeeScript](https://coffeescript.org/)
*   [Docker](https://www.docker.com/)
*   [FFmpeg](https://ffmpeg.org/)
## Empezando

Sigue estos pasos para configurar y ejecutar el proyecto en tu entorno local.

### Prerrequisitos

Asegúrate de tener los siguientes entornos o herramientas instaladas y configuradas:

*   **Entornos de Trabajo Soportados:**
    *   GitHub Codespaces - Insiders
    *   Ubuntu 24.04 LTS (o similar con acceso sudo/root)
    *   Otras distribuciones oficiales de Ubuntu LTS como Xubuntu
*   **Docker:** Necesario para construir y ejecutar los contenedores.
*   **Git:** Para clonar el repositorio.
*   **Make:** Para usar los comandos simplificados del `Makefile`.

### Instalación

1.  **Clona el repositorio:**
    ```bash
    git clone https://github.com/ElProConLag/node-rtsp-rtmp-server.git
    cd node-rtsp-rtmp-server
    ```

2.  **Crea la red Docker dedicada:**
    Esta red permitirá que los contenedores se comuniquen entre sí.
    ```bash
    docker network create rtmpnet
    ```

## Uso

A continuación se detallan los pasos para desplegar el servidor y los clientes.

### Desplegar el Servidor RTMP/HTTP

El servidor RTMP escuchará en el puerto `1935` y el servidor HTTP (para la página `index.html`) en el puerto `80`.

```bash
make build && make console
```
Este comando construye la imagen Docker del servidor (si aún no está construida) y luego lo inicia en modo interactivo. Los logs del servidor se mostrarán en esta consola.

### Desplegar Cliente Emisor (Cliente 1)

Este cliente utilizará FFmpeg para enviar un stream de video (ej. `bigbuckbunny`) al servidor RTMP.

1.  **Construye la imagen del cliente emisor:**
    ```bash
    docker build -f Dockerfile.cliente1 -t ffmpeg-client1 .
    ```

2.  **Ejecuta el cliente emisor:**
    ```bash
    docker run -d --name ffmpeg-client1 --add-host host.docker.internal:host-gateway --network rtmpnet ffmpeg-client1
    ```
    Esto enviará el stream a `rtmp://host.docker.internal:1935/live/bigbuckbunny`.

### Obtener direcciones IP de contenedores activos

Para conocer la IP asignada a un contenedor en la red Docker `rtmpnet`, ejecuta:

```bash
# Lista contenedores en ejecución
docker ps
# Muestra la IP de un contenedor por nombre o ID
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' <nombre_o_id_contenedor>
```

### Desplegar Cliente Receptor (Cliente 2)

Este cliente utilizará FFmpeg para conectarse al stream `live/bigbuckbunny` del servidor RTMP y guardarlo en un archivo `grabacion.flv` dentro del contenedor.

1.  **Construye la imagen del cliente receptor:**
    ```bash
    docker build -f Dockerfile.cliente2 -t ffmpeg-client2 .
    ```

2.  **Ejecuta el cliente receptor:**
    ```bash
    docker run -d --name ffmpeg-client2 --add-host host.docker.internal:host-gateway --network rtmpnet ffmpeg-client2
    ```

### Captura de Red

Para analizar el tráfico RTMP (u otro tráfico de red), puedes usar `tcpdump`.

```bash
sudo timeout 30 tcpdump -i any -w tcpdump_capture.pcap
```

## Licencia

Distribuido bajo la Licencia MIT. Ver `LICENSE` para más información.

## Scripts de Pruebas y Ataques

Esta sección documenta los scripts de Python utilizados para probar la robustez y seguridad del servidor RTMP.

### `rtmp_dos.py`

Este script simula un ataque de denegación de servicio (DoS) contra el servidor RTMP. Abre una gran cantidad de conexiones TCP (por defecto, 10,000), envía un comando `publish` en cada una y las mantiene abiertas para agotar los recursos del servidor. Intenta ajustar automáticamente el límite de descriptores de archivo (`ulimit`) del sistema para permitir un gran número de conexiones simultáneas.

### `scapy_rtmp_hijack.py`

Utiliza la biblioteca Scapy para construir y enviar paquetes RTMP a bajo nivel. Su objetivo es intentar un secuestro de stream (`hijacking`) enviando un comando `publish` para un stream que se asume ya está activo. Este script opera a un nivel más bajo que un cliente RTMP estándar, lo que permite omitir o alterar pasos del protocolo.

### `scapy_rtmp_play_before_connect.py`

Script de prueba diseñado para verificar la robustez del servidor. Envía comandos RTMP en un orden anómalo (un comando `play` antes del `connect` requerido) para observar cómo el servidor maneja peticiones fuera de secuencia.

Comportamiento esperado: el servidor debería rechazar la solicitud y no permitir la reproducción del stream.

Comportamiento real: El código del servidor lanza un error al intentar procesar un tipo de dato AMF0 desconocido, lo que indica que el servidor no está manejando correctamente este caso anómalo.

```text
2025-07-05 00:36:32.423 [rtmp:handshake] warning: unknown message format, assuming format 1
2025-07-05 00:36:32.427 [rtmp:client=F99g1HEY] requested stream undefined/bigbuckbunny
2025-07-05 00:36:32.427 [rtmp:client=F99g1HEY] error: stream not found: undefined/bigbuckbunny
2025-07-05 00:36:32.433 [rtmp] error parsing AMF0 command (maybe a bug); buf:
2025-07-05 00:36:32.433 <Buffer 03 02 00 03 61 70 70 02 00 04 6c 69 76 65 02 00 04 74 79 70 65 02 00 0a 6e 6f 6e 70 72 69 76 61 74 65 02 00 00 00 00 09>
/app/server.coffee:46
    throw err;
    ^

Error: Unknown AMF0 data type: undefined
    at parseAMF0Data (/app/rtmp.coffee:295:11)
    at parseAMF0Object (/app/rtmp.coffee:207:16)
    at parseAMF0Data (/app/rtmp.coffee:276:14)
    at parseAMF0CommandMessage (/app/rtmp.coffee:248:16)
    at /app/rtmp.coffee:2661:32
    at RTMPSession.handleData (/app/rtmp.coffee:2682:7)
    at Socket.<anonymous> (/app/rtmp.coffee:2717:23)
    at emitOne (events.js:77:13)
    at Socket.emit (events.js:169:7)
    at readableAddChunk (_stream_readable.js:153:18)
    at Socket.Readable.push (_stream_readable.js:111:10)
    at TCP.onread (net.js:540:20)
```

### `scapy_capture.py`

Una herramienta de captura de paquetes de red que utiliza Scapy. Escucha en una interfaz de red específica, captura todo el tráfico y guarda un análisis detallado de cada paquete en el archivo `packet_capture.txt`. Es útil para depurar y analizar las interacciones de red en tiempo real.