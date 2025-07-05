#!/usr/bin/env python3
from scapy.all import *
import sys
import os
import socket # Importar la biblioteca socket estándar
import struct
import time

# --- Configuración ---
# IP del servidor RTMP (el contenedor)
server_ip = "172.17.0.1" 
# Puerto del servidor RTMP
server_port = 1935
# Interfaz de red a usar (detectada dinámicamente para la red Docker 'rtmpnet').
def get_docker_bridge_interface(network_name="rtmpnet"):
    import subprocess
    try:
        # Obtener el ID de la red Docker
        result = subprocess.run([
            "docker", "network", "inspect", network_name, "--format", "{{.Id}}"
        ], capture_output=True, text=True, check=True)
        net_id = result.stdout.strip()
        if len(net_id) >= 12:
            return f"br-{net_id[:12]}"
    except Exception as e:
        print(f"[!] No se pudo detectar la interfaz de red de Docker automáticamente: {e}")
    # Fallback: usar docker0 o dejar vacío
    return "docker0"

net_interface = get_docker_bridge_interface()

# Carga útil (payload) del comando RTMP 'connect'.
# Se ha modificado tcUrl para apuntar directamente a la IP del servidor,
# ya que el script ahora se ejecuta desde el host.
rtmp_payload = (
    b'\x02\x00\x07connect\x00?\xf0\x00\x00\x00\x00\x00\x00\x03'
    b'\x00\x03app\x02\x00\x04live\x00\x04type\x02\x00\nnonprivate'
    b'\x00\x08flashVer\x02\x00$FMLE/3.0 (compatible; Lavf58.76.100)'
    b'\x00\x05tcUrl\x02\x00' + f'rtmp://{server_ip}:{server_port}/live'.encode('utf-8') + b'\x00\x00\t'
)

def simulate_rtmp_connection():
    """
    Simula una conexión RTMP usando un socket TCP estándar para la conexión
    y Scapy para la manipulación de los datos.
    """
    print(f"[*] Iniciando simulación de conexión RTMP hacia {server_ip}:{server_port}")
    
    # Especificamos la interfaz de red globalmente para Scapy
    conf.iface = net_interface
    print(f"[*] Usando interfaz: {conf.iface}")

    sock = None  # Inicializar sock a None
    try:
        # --- 1. Crear y conectar un socket TCP estándar ---
        print("\n[*] Creando y conectando socket TCP estándar...")
        # Usamos la biblioteca 'socket' para crear una conexión TCP fiable.
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10) # Aumentar timeout para la conexión
        sock.connect((server_ip, server_port))
        print("[*] Handshake TCP completado exitosamente a través del SO.")

        # --- 2. Realizar handshake RTMP ---
        print("\n[*] Realizando handshake RTMP...")
        # C0 + C1
        c0 = b'\x03'
        c1_time = struct.pack('>I', int(time.time()))
        c1_zero = b'\x00' * 4
        c1_random = os.urandom(1528)
        c1 = c1_time + c1_zero + c1_random
        print("[*] Enviando C0+C1...")
        sock.sendall(c0 + c1)
        # esperar S0+S1+S2
        print("[*] Esperando S0+S1+S2 del servidor...")
        s0 = sock.recv(1)
        s1 = sock.recv(1536)
        s2 = sock.recv(1536)
        if not s0 or not s1 or not s2:
            print("[!] El servidor no envió la respuesta completa del handshake.")
            return
        print("[*] Handshake S0+S1+S2 recibido.")
        # enviar C2 (eco de S1 con nuevo timestamp)
        c2_time = struct.pack('>I', int(time.time()))
        c2 = s1[:4] + c2_time + s1[8:]
        print("[*] Enviando C2...")
        sock.sendall(c2)
        print("[*] Handshake RTMP completado.")
        # --- 3. Envolver el socket con StreamSocket de Scapy ---
        # Le pasamos el socket ya conectado a Scapy para que lo use.
        tcp_socket = StreamSocket(sock, basecls=Raw)

        # --- 4. Enviar datos RTMP ---
        # Primero, ajustar el tamaño de chunk para evitar fragmentación
        print("\n[*] Enviando Set Chunk Size (4096)...")
        # Construir mensaje de control: Set Chunk Size
        scs_size = 4096
        # Basic Header: fmt=0, csid=2
        scs_basic = b"\x02"
        # Message Header: timestamp=0, length=4, typeID=0x01, streamID=0
        scs_header = b"\x00\x00\x00" + (4).to_bytes(3, 'big') + b"\x01" + (0).to_bytes(4, 'little')
        scs_payload = scs_size.to_bytes(4, 'big')
        scs_msg = scs_basic + scs_header + scs_payload
        tcp_socket.send(Raw(load=scs_msg))
        print("[*] Set Chunk Size enviado.")

        print("\n[*] Enviando comando RTMP 'connect' a través de Scapy...")
        
        # Construir mensaje RTMP: chunk básico + encabezado de mensaje + payload AMF
        payload = rtmp_payload
        payload_len = len(payload)
        # Basic Header: fmt=0, csid=3
        basic_header = b"\x03"
        # Message Header: timestamp(3 bytes), message length(3 bytes), type=0x14(AMF0 command), stream ID (4 bytes little endian)
        msg_header = b"\x00\x00\x00" + payload_len.to_bytes(3, 'big') + b"\x14" + (0).to_bytes(4, 'little')
        rtmp_message = basic_header + msg_header + payload
        tcp_socket.send(Raw(load=rtmp_message))
        print("[*] Comando 'connect' enviado.")
        # Leer respuesta completa del socket
        try:
            buffer = sock.recv(4096)
        except socket.timeout:
            print("[!] Timeout al leer respuesta del servidor.")
            return
        if not buffer:
            print("[!] No se recibió ningún dato del servidor.")
            return
        # Parsear múltiples chunks RTMP concatenados para extraer la carga AMF0 (typeID=0x14)
        pos = 0
        amf_payload = None
        while pos + 12 <= len(buffer):
            basic = buffer[pos]
            pos += 1
            # Encabezado de mensaje
            timestamp = int.from_bytes(buffer[pos:pos+3], 'big')
            pos += 3
            msg_len = int.from_bytes(buffer[pos:pos+3], 'big')
            pos += 3
            msg_type = buffer[pos]
            pos += 1
            stream_id = int.from_bytes(buffer[pos:pos+4], 'little')
            pos += 4
            # Extraer carga
            if pos + msg_len > len(buffer):
                break
            payload_data = buffer[pos:pos+msg_len]
            pos += msg_len
            if msg_type == 0x14:
                amf_payload = payload_data
                break
        if amf_payload is None:
            print("[!] No se encontró respuesta AMF0 del servidor.")
            return
        print("\n[*] Carga AMF0 recibida, procesando... ")
        data = amf_payload

        # === Parsear encabezado RTMP y decodificar payload AMF0 sin PyAMF ===
        # Parser AMF0 simple
        def read_amf0(buf, pos=0):
            # Parser AMF0 minimal
            if pos >= len(buf):
                return None, pos
            t = buf[pos]
            pos += 1
            # String
            if t == 0x02:
                if pos + 2 > len(buf):
                    return None, pos
                length = struct.unpack('>H', buf[pos:pos+2])[0]
                pos += 2
                if pos + length > len(buf):
                    return None, pos
                try:
                    elem = buf[pos:pos+length].decode('utf-8')
                except UnicodeDecodeError:
                    elem = buf[pos:pos+length].decode('utf-8', errors='ignore')
                pos += length
                return elem, pos
            # Number
            elif t == 0x00:
                if pos + 8 > len(buf):
                    return None, pos
                elem = struct.unpack('>d', buf[pos:pos+8])[0]
                pos += 8
                return elem, pos
            # Boolean
            elif t == 0x01:
                if pos + 1 > len(buf):
                    return None, pos
                elem = bool(buf[pos])
                pos += 1
                return elem, pos
            # Object
            elif t == 0x03:
                obj = {}
                while pos + 2 <= len(buf):
                    key_len = struct.unpack('>H', buf[pos:pos+2])[0]
                    pos += 2
                    # End of object marker (0x000009)
                    if key_len == 0:
                        if pos < len(buf) and buf[pos] == 0x09:
                            pos += 1
                        break
                    if pos + key_len > len(buf):
                        break
                    try:
                        key = buf[pos:pos+key_len].decode('utf-8')
                    except UnicodeDecodeError:
                        key = buf[pos:pos+key_len].decode('utf-8', errors='ignore')
                    pos += key_len
                    val, new_pos = read_amf0(buf, pos)
                    if val is not None:
                        obj[key] = val
                        pos = new_pos
                    else:
                        break
                return obj, pos
            # Null or unsupported
            elif t == 0x05:
                return None, pos
            else:
                return f'<Unsupported AMF0 0x{t:02x}>', pos

        # Decodificar todos los elementos AMF0
        pos = 0
        elements = []
        # Limitar a los primeros 4 elementos: nombre, txnID, objeto resultado, objeto status
        while pos < len(data) and len(elements) < 4:
            val, new_pos = read_amf0(data, pos)
            if val is None:
                break
            elements.append(val)
            pos = new_pos
        print("[*] Elementos AMF0 recibidos:")
        for e in elements:
            print("   ", e)
    
    except socket.timeout:
        print("[!] Error: Timeout durante la conexión. El servidor no respondió.")
    except ConnectionRefusedError:
        print("[!] Error: Conexión rechazada. ¿Está el servidor RTMP corriendo en el puerto correcto?")
    except Exception as e:
        print(f"[!] Ocurrió un error inesperado: {e}")
    finally:
        # --- 4. Cerrar el socket ---
        if sock:
            print("\n[*] Cerrando el socket.")
            sock.close()
    
    print("\n[*] Simulación finalizada.")


if __name__ == "__main__":
    # Scapy requiere privilegios de root para enviar paquetes en la mayoría de los sistemas.
    if os.geteuid() != 0:
        print("[!] Error: Este script necesita privilegios de root para funcionar.")
        print("    Por favor, ejecútalo con 'sudo'.")
        sys.exit(1)
        
    simulate_rtmp_connection()
