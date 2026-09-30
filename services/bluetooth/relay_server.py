import socket
import threading
import sys

# Integrated Avodah LLC - Host Server Network Relay Utility
# Location: Lawrence, KS
# Purpose: Streamlined multi-interface compliance routing bridge

LOCAL_HOST = '0.0.0.0'
LOCAL_PORT = 9999
TARGET_HOST = '192.168.1.1'  # Target network appliance / router
TARGET_PORT = 9999          # Target proxy/service port

def handle_client(client_socket, remote_socket):
    def forward(source, destination):
        try:
            while True:
                data = source.recv(4096)
                if not data:
                    break
                destination.sendall(data)
        except Exception:
            pass
        finally:
            source.close()
            destination.close()

    # Create bidirectional forwarding threads
    t1 = threading.Thread(target=forward, args=(client_socket, remote_socket))
    t2 = threading.Thread(target=forward, args=(remote_socket, client_socket))
    t1.start()
    t2.start()

def start_relay_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind((LOCAL_HOST, LOCAL_PORT))
        server.listen(10)
        print(f"[+] Integrated Avodah Network Relay active on {LOCAL_HOST}:{LOCAL_PORT}")
        print(f"[*] Forwarding traffic streams to target node {TARGET_HOST}:{TARGET_PORT}...")
        
        while True:
            client_sock, client_addr = server.accept()
            print(f"[+] Inbound connection established from interface: {client_addr[0]}:{client_addr[1]}")
            
            remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                remote_sock.connect((TARGET_HOST, TARGET_PORT))
                handler = threading.Thread(target=handle_client, args=(client_sock, remote_sock))
                handler.start()
            except Exception as e:
                print(f"[-] Failed to connect to target node {TARGET_HOST}:{TARGET_PORT}: {e}")
                client_sock.close()
                
    except Exception as e:
        print(f"[-] Relay server binding error: {e}")
    finally:
        server.close()

if __name__ == "__main__":
    start_relay_server()
