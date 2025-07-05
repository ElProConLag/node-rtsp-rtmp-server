from scapy.all import *
from scapy.layers.inet import IP, TCP
from scapy.packet import Raw

def modify_packet(pkt):
    if pkt.haslayer(TCP) and pkt.haslayer(Raw) and pkt[TCP].dport == 1935:
        payload = bytearray(pkt[Raw].load)
        if len(payload) > 8 and (payload[0] & 0x3F) == 0:  # Solo chunks tipo 0 tienen Message Type ID en posición 8
            payload[8] = 0xFF  # Message Type ID inválido
            new_pkt = pkt[IP] / TCP(sport=pkt[TCP].sport, dport=pkt[TCP].dport, flags="PA") / Raw(load=payload)
            send(new_pkt, verbose=0)
            print("Paquete modificado (Message Type ID inválido) enviado!")

import subprocess
import os

def get_docker_bridge_interface(network_name="rtmpnet"):
    try:
        result = subprocess.run([
            "docker", "network", "inspect", network_name, "--format", "{{.Id}}"
        ], capture_output=True, text=True, check=True)
        net_id = result.stdout.strip()
        if len(net_id) >= 12:
            return f"br-{net_id[:12]}"
    except Exception as e:
        print(f"[!] No se pudo detectar la interfaz de red de Docker automáticamente: {e}")
    return "docker0"

if __name__ == "__main__":
    iface = get_docker_bridge_interface()
    print(f"[INFO] Starting sniff on interface: {iface} (tcp port 1935)")
    sniff(filter="tcp port 1935", prn=modify_packet, iface=iface)