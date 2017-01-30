"""
This is the window where the user can read the chat.
server ---> client_output
"""
import socket

def isDone():
    with open("conn_info.txt", 'r+') as file:
        value = file.readlines[3].replace('\n', '')
        file.close()
    return bool(value)

def Listen():
    print("Starting Program")
    with open("conn_info.txt", 'r') as file:
        lines = file.readlines()
        IP = lines[0]
        port = lines[2]
        file.close()
    raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    raw_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    raw_socket.bind(('', int(port)))  # keep for now, might bind to external address????
    raw_socket.listen(5)
    recv_sock, sockname = raw_socket.accept()
    print("Connected to Server: ", sockname)
    recv_sock.shutdown(socket.SHUT_WR)
    while not isDone():
        message = recv_sock.recv(4096)  # figure out correct byte value
        if message:
            print(message.decode('ascii'))
    recv_sock.close()
    raw_socket.close()

if __name__ == "__main__":
    Listen()
