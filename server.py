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

        r, w, e = next(selectGenerator())

        for sock in r:
            if sock is listener:  # add new socket
                inSock, address = listener.accept()
                inSock.shutdown(socket.SHUT_WR)
                outSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
              ###  outSock.setblocking(0)
                outSock.connect((address[0], SEND_PORT))
                Connected_Clients[inSock] = [outSock, ""] #worry about username later
                recv_buffer[inSock] = None
                send_buffer[outSock] = None
            else: #receive from socket
                fullStr = sock.recv(1024)
                if recv_buffer[sock]: #data already exists in buffer.
                    recv_buffer[sock][1] += fullStr.decode('ascii')
                    if len(recv_buffer[sock][1]) == recv_buffer[sock][0]:
                        doNext = inputHandler(recv_buffer[sock][1]) #temporary???? Function returns an array.
                        recv_buffer[sock] = None #empty the buffer. being transfered to send buffer
                        if doNext[0] == "message": #not a command. user is chatting.
                            for client in send_buffer:
                                send_buffer[client] = doNext[1]
                            print("Send Buffer: \n ", send_buffer)
                    else:
                        print("Message not done")
                    pass


                else: #first part of transmission. get byte size and rest of chunk.
                    sizeOfMessage = header.unpack(fullStr[0:header.size])[0]
                    recv_buffer[sock] = (sizeOfMessage, fullStr[header.size:].decode('ascii'))
                    if len(recv_buffer[sock][1]) == recv_buffer[sock][0]:
                        doNext = inputHandler(recv_buffer[sock][1]) #temporary???? Function returns an array.
                        recv_buffer[sock] = None #empty buffer. being transferred to send buffer.
                        if doNext[0] == "message": #not a command. user is chatting.
                            for client in send_buffer:
                                send_buffer[client] = doNext[1]
                            print("Send Buffer: \n ", send_buffer)
                    else:
                        print("Message not done")
                    pass
        for sock in w:
            if send_buffer[sock]:
                toSend = send_buffer[sock].encode('ascii')
                sock.sendall(toSend)
                send_buffer[sock] = None
                print(toSend, " sent to output")
                pass
        for sock in e:
            pass


def noneFilter(list):
    returnList = []
    for elem in list:
        if elem:
            returnList.append(elem)
    return returnList



def createListenSocket():
    """
    Creates the server's listening socket.
    Server listens on all addresses ('') at port 1060
    :return: sslSocket object (eventually, right now, just a regular socket object)
    """
    raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    #raw_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    raw_socket.setblocking(0)

    raw_socket.bind(('', LISTEN_PORT))

    raw_socket.listen(5)
    return raw_socket
    # more will be added to the ssl socket for security purposes


def inputHandler(strInput): # returns an array
    contentArray = strInput.split(":`:")
    if contentArray[0][0] == "`":
        keyword = contentArray[0][1:]
        args = contentArray[1:]
        if keyword == "@@output":  #special command. "Private"ly used by _control to tell server
                                    # where to send output.

            return ["set", args[0]]

    else:
        contentArray.insert(0, "message")
        return contentArray




def selectGenerator():
    while True:  #probably add a condition later.

        inputSockets = list(Connected_Clients.keys())
        outputSockets = []
        for array in list(Connected_Clients.values()):
            outputSockets.append(array[0])

       # print(inputSockets, "\n", outputSockets)
        inputSockets2 = noneFilter(inputSockets)
        r, w, e = select.select(inputSockets2, noneFilter(outputSockets), inputSockets2)
        #print("Past")
        yield r, w, e



if __name__ == "__main__":
    messageFile = open("Messages.txt", 'r')
    Server_Messages = messageFile.readlines()
    messageFile.close()
    for i in range(0, len(Server_Messages)):
        Server_Messages[i] = Server_Messages[i].replace('\n', '')

    RoomList = Room.LoadRooms()
    listSocket = createListenSocket()

    Connected_Clients[listSocket] = [None, "@@server"]  #if it doesn't like None(no fd), then set to itself, and check in

                                            # other functions if equal to self
    Main(listSocket)

