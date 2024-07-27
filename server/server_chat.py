import threading
import socket

HOST = "localhost"
PORT = 12345

SERVER = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
SERVER.bind((HOST, PORT))
SERVER.listen()

clients = {}  # Dictionary to map nicknames to clients
admin_addresses = ["localhost"]

def broadcast_msg(message):
    for client, _ in clients.values():
        try:
            client.send(message.encode("utf-8"))
        except Exception as e:
            print(f"Error broadcasting message: {e}")

def add_admin(address, nickname):
    try:
        admin_addresses.append(address)
        broadcast_msg(f"{nickname} is promoted to an admin")
    except Exception as e:
        print(f"Error adding admin: {e}")

def send_private_msg(message, sender_nickname, recipient_nickname):
    recipient_client, _ = clients.get(recipient_nickname, (None, None))
    if recipient_client:
        try:
            recipient_client.send(f"Private from {sender_nickname}: {message}".encode("utf-8"))
        except Exception as e:
            print(f"Error sending private message to {recipient_nickname}: {e}")
    else:
        sender_client, _ = clients.get(sender_nickname, (None, None))
        if sender_client:
            sender_client.send(f"{recipient_nickname} is not connected.".encode("utf-8"))

def admin_kick(kick_nickname):
    kick_client, _ = clients.get(kick_nickname, (None, None))
    if kick_client:
        try:
            kick_client.close()
        except Exception as e:
            print(f"Error kicking client {kick_nickname}: {e}")
        del clients[kick_nickname]
        broadcast_msg(f"{kick_nickname} has been kicked from the chat")

def client_handler(client, address, nickname):
    while True:
        try:
            message = client.recv(1024).decode("utf-8")
            if not message:
                raise Exception("Client disconnected")

            if message.startswith("/kick"):
                if address[0] in admin_addresses:
                    parts = message.split(' ')
                    kick_nickname = parts[1]
                    if kick_nickname in clients.keys():
                        admin_kick(kick_nickname)
                    else:
                        client.send("Nickname not found".encode("utf-8"))
                else:
                    client.send("Only admins have /kick privileges".encode("utf-8"))
                    
            elif message.startswith("/addadmin"):
                if address[0] in admin_addresses:
                    parts = message.split(' ')
                    admin_nickname = parts[1]
                    if admin_nickname in clients.keys():
                        _, admin_address = clients[admin_nickname]
                        add_admin(address=admin_address[0], nickname=admin_nickname)
                    else:
                        client.send("Nickname not found".encode("utf-8"))
                else:
                    client.send("Only admins have /addadmin privileges".encode("utf-8"))

            elif message.startswith("/listusers"):
                users = list(clients.keys())
                client.send(f"All users: {users}".encode("utf-8"))
                

            elif message.startswith("/listadmins"):
                if address[0] in admin_addresses:
                    admins = [nickname for nickname, (client, addr) in clients.items() if addr[0] in admin_addresses]
                    client.send(f"All admins: {admins}".encode("utf-8"))
                else:
                    client.send("Only admins have /listadmins privileges".encode("utf-8"))

            elif message.startswith("/private"):
                parts = message.split(' ', 2)
                if len(parts) >= 3:
                    recipient_nickname = parts[1]
                    private_message = parts[2]
                    send_private_msg(private_message, nickname, recipient_nickname)
                else:
                    client.send("Invalid /private command format. Use /private <recipient> <message>".encode("utf-8"))

            else:
                broadcast_msg(f"{nickname}: {message}")

        except Exception as e:
            print(f"Error handling client {nickname}: {e}")
            clients.pop(nickname, None)
            client.close()
            broadcast_msg(f"{nickname} has left the chat")
            break

def chat_main():
    print(f"Server is listening on {HOST}:{PORT}")
    try:
        while True:
            client, address = SERVER.accept()
            print(f"Client joined from address: {address}")

            client.send("NICKNAME".encode("utf-8"))
            nickname = client.recv(1024).decode("utf-8")

            while nickname in clients:
                client.send("NICKNAME in use, please change".encode("utf-8"))
                nickname = client.recv(1024).decode("utf-8")

            clients[nickname] = (client, address)
            print(f"Nickname of the client is {nickname}")

            broadcast_msg(f"{nickname} joined the chat")

            client_thread = threading.Thread(target=client_handler, args=(client, address, nickname))
            client_thread.start()
    except KeyboardInterrupt:
        print("Server is shutting down.")
    finally:
        for client, _ in clients.values():
            client.close()
        SERVER.close()


