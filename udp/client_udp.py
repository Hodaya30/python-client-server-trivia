import socket

SERVER_IP = "127.0.0.1"
PORT = 8821
MAX_MSG_SIZE = 1024
import random
my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
my_socket.sendto("Omer".encode(), (SERVER_IP, PORT))
(response, remote_address) = my_socket.recvfrom(MAX_MSG_SIZE)
data = response.decode()
print("The server sent " + data)
def special_sendto(socket_object, response, client_address):
    fail = random.randint(1, 3)
    if not (fail == 1):
        socket_object.sendto(response.encode(), client_address)
    else:
        print("Oops")
my_socket.close()