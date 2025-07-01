#!/usr/bin/env python3
from scapy.all import *
import socket
import struct
import os
import time

"""
Script Scapy: Envía comandos RTMP en orden no estándar (ejemplo: 'play' antes de 'connect')
No sobrescribe scripts existentes.
"""

# Configuración
server_ip = "172.17.0.1"
server_port = 1935
net_interface = "br-fa98ff1cadf0"

# Utilidades para construir mensajes AMF0

def amf0_string(s):
    s = s.encode('utf-8')
    return b'\x02' + struct.pack('>H', len(s)) + s

def amf0_number(n):
    return b'\x00' + struct.pack('>d', float(n))

def amf0_null():
    return b'\x05'

def build_play_command(stream_name="test", txn_id=1):
    # play, txn_id, null, stream_name
    return amf0_string("play") + amf0_number(txn_id) + amf0_null() + amf0_string(stream_name)

def build_connect_command(app="live", txn_id=1):
    # connect, txn_id, object
    obj = (
        b'\x03' +
        amf0_string("app") + amf0_string(app) +
        amf0_string("type") + amf0_string("nonprivate") +
        amf0_string("") + b'\x00\x00\x09'  # end of object
    )
    return amf0_string("connect") + amf0_number(txn_id) + obj

# Construcción de mensajes RTMP

def build_rtmp_message(payload, msg_type=0x14, stream_id=0):
    # Basic Header: fmt=0, csid=3
    basic_header = b"\x03"
    # Message Header: timestamp(3), length(3), type(1), stream_id(4, little endian)
    msg_header = b"\x00\x00\x00" + len(payload).to_bytes(3, 'big') + bytes([msg_type]) + stream_id.to_bytes(4, 'little')
    return basic_header + msg_header + payload


def main():
    print(f"[*] Enviando comando 'play' antes de 'connect' al servidor RTMP {server_ip}:{server_port}")
    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((server_ip, server_port))
        # Handshake RTMP estándar
        c0 = b'\x03'
        c1_time = struct.pack('>I', int(time.time()))
        c1_zero = b'\x00' * 4
        c1_random = os.urandom(1528)
        c1 = c1_time + c1_zero + c1_random
        sock.sendall(c0 + c1)
        s0 = sock.recv(1)
        s1 = sock.recv(1536)
        s2 = sock.recv(1536)
        c2 = s1[:4] + struct.pack('>I', int(time.time())) + s1[8:]
        sock.sendall(c2)
        # Envolver socket con Scapy
        tcp_socket = StreamSocket(sock, basecls=Raw)
        # 1. Enviar 'play' antes de 'connect'
        play_payload = build_play_command(stream_name="bigbuckbunny", txn_id=1)
        play_msg = build_rtmp_message(play_payload, msg_type=0x14, stream_id=1)
        print("[*] Enviando comando 'play' (antes de 'connect')...")
        tcp_socket.send(Raw(load=play_msg))
        # Esperar respuesta
        try:
            resp = sock.recv(4096)
            if resp:
                print(f"[*] Respuesta tras 'play': {resp[:32].hex()} ... [{len(resp)} bytes]")
            else:
                print("[*] Sin respuesta tras 'play'")
        except socket.timeout:
            print("[*] Timeout esperando respuesta tras 'play'")
        # 2. Enviar 'connect' después
        connect_payload = build_connect_command(app="live", txn_id=2)
        connect_msg = build_rtmp_message(connect_payload, msg_type=0x14, stream_id=0)
        print("[*] Enviando comando 'connect'...")
        tcp_socket.send(Raw(load=connect_msg))
        try:
            resp2 = sock.recv(4096)
            if resp2:
                print(f"[*] Respuesta tras 'connect': {resp2[:32].hex()} ... [{len(resp2)} bytes]")
            else:
                print("[*] Sin respuesta tras 'connect'")
        except socket.timeout:
            print("[*] Timeout esperando respuesta tras 'connect'")
    except Exception as e:
        print(f"[!] Error: {e}")
    finally:
        if sock:
            print("[*] Cerrando el socket.")
            sock.close()
    print("[*] Script finalizado.")

if __name__ == "__main__":
    main()
