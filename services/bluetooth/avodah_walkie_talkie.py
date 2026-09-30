import socket
import threading
import sys

# Integrated Avodah LLC - Walkie-Talkie Secure Relay Node
# Purpose: Real-time peer-to-peer communication bridge between mobile client and PC host

HOST = '0.0.0.0'
PORT = 8899

def handle_peer(client_socket, address):
    print(f"\n[+] Secure audio/data link established with mobile unit: {address[0]}:{address[1]}")
    print("[*] Walkie-Talkie channel active. Type your transmission below (type 'exit' to close):\n")
    
    def receive_messages():
        while True:
            try:
                data = client_socket.recv(4096)
                if not data:
                    print("\n[-] Mobile unit disconnected.")
                    break
                message = data.decode('utf-8', errors='ignore')
                print(f"\n[Mobile Transmission Received] -> {message}")
                print("PC-Talkie> ", end="", flush=True)
            except Exception:
                break

    # Start listener thread for incoming mobile packets
    recv_thread = threading.Thread(target=receive_messages, daemon=True)
    recv_thread.start()

    # Send loop from PC to mobile
    try:
        while True:
            msg = input("PC-Talkie> ")
            if not msg.strip():
                continue
            client_socket.sendall(msg.encode('utf-8'))
            if msg.lower() == 'exit':
                break
    except Exception as e:
        print(f"[-] Transmission error: {e}")
    finally:
        client_socket.close()

def start_walkie_talkie_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind((HOST, PORT))
        server.listen(1)
        print(f"==================================================")
        print(f" INTEGRATED AVODAH LLC - WALKIE-TALKIE RELAY PORT ")
        print(f"==================================================")
        print(f"[*] Listening for mobile connection on port {PORT}...")
        
        client_socket, address = server.accept()
        handle_peer(client_socket, address)
        
    except Exception as e:
        print(f"[-] Server initialization error: {e}")
    finally:
        server.close()

if __name__ == "__main__":
    start_walkie_talkie_server()
