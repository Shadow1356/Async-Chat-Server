"""
Starts client_input and client_output. Gets _input text from files and sends to server
client_control -> server
"""

import os, sys, client_input, socket, client_output


outputDone = False

if sys.platform == "Windows":
    __dirPath = os.getcwd() + "\\messages\\"
else:
    __dirPath = os.getcwd() + "/messages/"

def connectToServer():
    with open("conn_info.txt", 'r') as file:
        IP, port = file.readlines()[0:2]
        file.close()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((IP, int(port)))
    print("Connected to ", IP, "with name: ", sock.getpeername())
    return sock


def sendNextMessage(sock):
    dirContents = os.listdir(__dirPath)
    if dirContents:
        fileName = sorted(dirContents)[0]
        file = open((__dirPath+fileName), 'r')
        message = file.read()
        file.close()
        os.remove((__dirPath+fileName))
        if message == "`exit":
            print("In exit condition")
            return True
        print("getting here")
        sock.sendall(message.encode("ascii"))
        print("Sent ", message, "to", sock)
        return False




if __name__ == "__main__":
    global outputDone
    listener = connectToServer()
    # startOutput()
    exitCode = False
    print("entering Loop")
    while not exitCode:
        exitCode = sendNextMessage(listener)
    print('loop has exited')
    outputDone = True
    input()