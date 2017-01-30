import select, socket, Room, struct, commands

"""
Globals
"""
with open("conn_info.txt", 'r') as file:
    lines = file.readlines()

    LISTEN_PORT = int(lines[1])
    SEND_PORT = int(lines[2])

    header = struct.Struct(lines[4])
    file.close()
recv_buffer = {}  # client --> str
send_buffer = {}  # Room ---> str
Server_Messages = []

Connected_Clients = {}  # socket ---> [socket, str]




def Main(listener):
    while True:  # probably add condition later

        print("Hope I'm wrong")
        r, w, e = selectGenerator()
        print("Osik")
        for sock in r:
            print("Almost")
            if sock is listener:  # add new socket
                print("YAY!")
                inSock, address = listener.accept()
                inSock.shutdown(socket.SHUT_WR)
                Connected_Clients[inSock] = [None, ""]




def createListenSocket():
    """
    Creates the server's listening socket.
    Server listens on all addresses ('') at port 1060
    :return: sslSocket object (eventually, right now, just a regular socket object)
    """
    raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    #raw_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    raw_socket.setblocking(0)
    raw_socket.bind(('localhost', LISTEN_PORT))

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

            return ["set", args[0]]




def selectGenerator():
    while True:  #probably add a condition later.

        inputSockets = list(Connected_Clients.keys())
        outputSockets = []
        for array in list(Connected_Clients.values()):
            outputSockets.append(array[0])
        print(inputSockets, "\n", outputSockets)
        for r, w, e in select.select(inputSockets, outputSockets, inputSockets):
            print("Past")

            yield r, w, e


if __name__ == "__main__":
    messageFile = open("Messages.txt", 'r')
    Server_Messages = messageFile.readlines()
    messageFile.close()
    for i in range(0, len(Server_Messages)):
        Server_Messages[i] = Server_Messages[i].replace('\n', '')

    RoomList = Room.LoadRooms()
    listSocket = createListenSocket()
    Connected_Clients[listSocket] = [listSocket, "@@server"]  #if it doesn't like None(no fd), then set to itself, and check in

                                            # other functions if equal to self
    Main(listSocket)

