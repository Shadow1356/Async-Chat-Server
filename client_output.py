"""
This is the window where the user can read the chat.
server ---> client_output
"""
import socket

toBool = {"False": False, "True": True}


def isDone():
    with open("conn_info.txt", 'r+') as file:
        value = file.readlines()[3].replace('\n', '')
        file.close()
       # print(value)
    return toBool[value]

def Listen():
    with open("conn_info.txt", 'r') as file:
        lines = file.readlines()
        IP = lines[0]
        port = lines[2]
        file.close()
    raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    raw_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    raw_socket.bind(('', int(port)))
    raw_socket.listen(5)
    recv_sock, sockname = raw_socket.accept()
    recv_sock.shutdown(socket.SHUT_WR)
    print("Connected to Server: ", sockname)
    recv_sock.shutdown(socket.SHUT_WR)
    recv_sock.settimeout(0.0)
    print(recv_sock.gettimeout())
    done = False
   # x =1
    while not done:
    #    print("In Here", x)
     #   x+= 1
        try:
            message = recv_sock.recv(4096)  # figure out correct byte value
        except TimeoutError:
            break # Handle error later
        except BlockingIOError:
           # print("IN blocking error")
            continue
        if message:
            print(message.decode('ascii'))
            message = ""
            done = isDone()
    recv_sock.close()
    raw_socket.close()

if __name__ == "__main__":
    print("__ouptput")
    Listen()
