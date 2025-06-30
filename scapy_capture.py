#!/usr/bin/env python3
from scapy.all import *
import sys

# Define el archivo de salida
output_file = "packet_capture.txt"

def process_packet(packet):
    """
    Esta función se llama para cada paquete capturado.
    Añade la información detallada del paquete al archivo de salida.
    """
    with open(output_file, "a") as f:
        # Redirige la salida estándar al archivo para capturar la salida detallada de show()
        original_stdout = sys.stdout
        sys.stdout = f
        print(f"--- Paquete: {packet.summary()} ---")
        packet.show()  # Proporciona una vista detallada y verbosa del paquete
        print("\n" + "="*80 + "\n")
        sys.stdout = original_stdout

def main():
    """
    Función principal para iniciar el proceso de captura de paquetes.
    """
    interface = "br-fa98ff1cadf0"
    print(f"Iniciando captura de paquetes en la interfaz {interface}...")
    print(f"Los resultados detallados se guardarán en {output_file}")

    try:
        # Inicia la captura. prn es la función de devolución de llamada para cada paquete.
        # store=0 significa que no guardamos los paquetes en memoria.
        sniff(iface=interface, prn=process_packet, store=0)
    except Exception as e:
        print(f"Ocurrió un error: {e}")
        print("Asegúrate de ejecutar este script con suficientes privilegios (por ejemplo, sudo) y de que la interfaz existe.")

if __name__ == "__main__":
    # Limpia el archivo de salida al inicio del script
    with open(output_file, "w") as f:
        f.write("Registro de Captura de Paquetes de Scapy\n")
        f.write("="*80 + "\n\n")
    main()
