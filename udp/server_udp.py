import socket
import random
SERVER_IP = "0.0.0.0"
PORT = 8821
MAX_MSG_SIZE = 1024

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((SERVER_IP, PORT))
(client_message, client_address) = server_socket.recvfrom(MAX_MSG_SIZE)
data = client_message.decode()
print("Client sent: " + data)
response = "Hello " + data
server_socket.sendto(response.encode(), client_address)
def special_sendto(socket_object, response, client_address):
    fail = random.randint(1, 3)
    if not (fail == 1):
        socket_object.sendto(response.encode(), client_address)
    else:
        print("Oops")
server_socket.close()
