import select, socket, ssl

"""
Globals
"""
recv_buffer = {}
send_buffer = {}
Server_Messages = []
PORT_NUMBER = 1060

def createListenSocket():
    """
    Creates the server's listening socket.
    Server listens on all addresses ('') at port 1060
    :return: sslSocket object (eventually, right now, just a regular socket object)
    """
    raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    raw_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    raw_socket.bind(('', PORT_NUMBER))
    raw_socket.listen(5)
    return raw_socket
    # more will be added to the ssl socket for security purposes

def Main(listener):
    inSock, sockname = listener.accept()
    print("Connected to InputControl: ", str(sockname))
    inSock.shutdown(socket.SHUT_WR)
    outSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    outSock.connect(("192.168.1.132", 1065)) 
    print("Connected to Output: ", outSock.getpeername())
    outSock.shutdown(socket.SHUT_RD)
    message = inSock.recv(4096).decode("ascii")
    print("Received ", message)
    sendMessage = ("Received " + message + " From " + str(sockname)).encode("ascii")
    outSock.sendall(sendMessage)
    outSock.close()
    inSock.close()



def modifyGlobals():
    """
    To be run at startup of server.
    imports messages.txt, and maybe more.
    might do away with method and just move to server main program.
    """
    global Server_Messages
    messageFile = open("Messages.txt", 'r')
    Server_Messages = messageFile.readlines()
    messageFile.close()
    for i in range(0, len(Server_Messages)):
        Server_Messages[i] = Server_Messages[i].replace('\n', '')



if __name__ == "__main__":
    #modifyGlobals()
    listSocket = createListenSocket()
    while True:
        Main(listSocket)

