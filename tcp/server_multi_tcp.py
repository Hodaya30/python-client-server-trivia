import socket
import select

MAX_MSG_LENGTH = 10024
SERVER_IP = "0.0.0.0"
SERVER_PORT = 8820


def print_client_socket(client_sockets):
    for c in client_sockets:
        print("/t", c.getpeername())


def main():
    print("Setting up server...")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_IP, SERVER_PORT))
    server_socket.listen()
    print("Listening for clients...")
    client_sockets = []
    messages_to_send = []
    while True:
        ready_to_read, ready_to_write, in_error = select.select([server_socket] + client_sockets, client_sockets, [])
        for current_socket in ready_to_read:
            if current_socket is server_socket:
                (client_socket, client_address) = current_socket.accept()
                print("New client joined!", client_address)
                client_sockets.append(client_socket)
                print_client_socket(client_sockets)
            else:
                print("New data from client")
                try:
                    data = current_socket.recv(MAX_MSG_LENGTH).decode()
                    if data == "":
                        print("Connection closed")
                        client_sockets.remove(current_socket)
                        current_socket.close()
                        print_client_socket(client_sockets)
                    else:
                        print(data)
                        messages_to_send.append((current_socket, data))
                        print_client_socket(client_sockets)
                except:
                    print("Connection closed")
                    client_sockets.remove(current_socket)
                    current_socket.close()
                    print_client_socket(client_sockets)
            for message in messages_to_send:
                current_socket, data = message
                if current_socket in ready_to_write:
                    current_socket.send(data.encode())
                    messages_to_send.remove(message)


if __name__ == '__main__':
    main()
