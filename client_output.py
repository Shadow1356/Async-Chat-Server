"""
This is the window where the user can read the chat.
server ---> client_output
"""
import socket, client_control



def Listen():
    print("Starting Program")
    with open("conn_info.txt", 'r') as file:
        IP, port = file.readlines()[2:4]
        file.close()
    raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    raw_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    raw_socket.bind(('', int(port)))
    raw_socket.listen(5)
    recv_sock, sockname = raw_socket.accept()
    print("Connected to Server: ", sockname)
    recv_sock.shutdown(socket.SHUT_WR)
    while not client_control.outputDone:
        message = recv_sock.recv(4096)  # figure out correct byte value
        if message:
            print(message.decode('ascii'))
    recv_sock.close()
    raw_socket.close()

if __name__ == "__main__":
    Listen()
