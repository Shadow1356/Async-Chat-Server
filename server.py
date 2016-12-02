import select, socket, Room, struct, commands

"""
Globals
"""
with open("conn_info.txt", 'r') as file:
    lines = file.readlines()
    LISTEN_PORT = lines[1]
    SEND_PORT = lines[2]
    header = struct.Struct(lines[4])
    file.close()
recv_buffer = {}  # client --> str
send_buffer = {}  # Room ---> str
Server_Messages = []
Connected_Clients = {}  # socket ---> socket



def Main(listener):
    while True:  # probably add condition later
        r, w, e = selectGenerator()
        for sock in r:
            if sock is listener:  # add new socket
                inSock, address = listener.accept()
                inSock.shutdown(socket.SHUT_WR)



def createListenSocket():
    """
    Creates the server's listening socket.
    Server listens on all addresses ('') at port 1060
    :return: sslSocket object (eventually, right now, just a regular socket object)
    """
    raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    raw_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    raw_socket.bind(('', LISTEN_PORT))
    raw_socket.listen(5)
    return raw_socket
    # more will be added to the ssl socket for security purposes


def inputHandler(byteInput):
    contentArray = byteInput.decode("ascii")[header.size:].split(":`:")
    if contentArray[0][0] == "`":
        keyword = contentArray[0][1:]
        args = contentArray[1:]
        if keyword == "@@output":  #special command. "Private"ly used by _control to tell server
                                    # where to send output.
            return ['set', args]



def selectGenerator():
    while True:  #probably add a condition later.
        for r, w, e in select.select(list(Connected_Clients.keys()), list(Connected_Clients.values()), []):
            yield r, w, e


if __name__ == "__main__":
    messageFile = open("Messages.txt", 'r')
    Server_Messages = messageFile.readlines()
    messageFile.close()
    for i in range(0, len(Server_Messages)):
        Server_Messages[i] = Server_Messages[i].replace('\n', '')
    listSocket = createListenSocket()
    Connected_Clients[listSocket] = None  #if it doesn't like None(no fd), then set to itself, and check in
                                            # other functions if equal to self
    Main(listSocket)

