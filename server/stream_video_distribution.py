import socket
import threading

DIST_HOST = "localhost"
DIST_PORT = 12346
BUFFER_SIZE = 2**16
HOST_ADDRESS = None
CLIENTS = []

def handle_host(host_socket):
    """Receive data from the host and distribute it to all connected clients."""
    while True:
        try:
            screen_data = host_socket.recv(BUFFER_SIZE)
            if not screen_data:
                break
            for client_socket in CLIENTS:
                client_socket.sendall(screen_data)
        except Exception as e:
            print(f"Error receiving data from host: {e}")
            host_socket.close()
            break

def handle_client(client_socket):
    """Keep the client connection alive and handle client-specific communication."""
    try:
        client_socket.sendall(b'Connected to the distribution server\n')
        while True:
            # The server could handle client-specific communication here.
            pass
    except Exception as e:
        print(f"Error handling client: {e}")
        client_socket.close()
        CLIENTS.remove(client_socket)

def dist_video_main():
    """Main function to set up and run the distribution server."""
    DIST_SERVER = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    DIST_SERVER.bind((DIST_HOST, DIST_PORT))
    DIST_SERVER.listen(5)

    print(f"Distribution server is listening for connections at {DIST_HOST}:{DIST_PORT}")

    while True:
        client_socket, addr = DIST_SERVER.accept()
        global HOST_ADDRESS
        if HOST_ADDRESS is None:
            # The first connection is assumed to be the host.
            HOST_ADDRESS = addr[0]
            print(f"Host {addr} connected")
            host_thread = threading.Thread(target=handle_host, args=(client_socket,))
            host_thread.start()
        else:
            # Subsequent connections are clients.
            print(f"Client {addr} connected")
            CLIENTS.append(client_socket)
            client_thread = threading.Thread(target=handle_client, args=(client_socket,))
            client_thread.start()

if __name__ == "__main__":
    dist_video_main()
