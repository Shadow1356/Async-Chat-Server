import select, socket, Room, struct, commands, miscellaneous

"""
Globals
"""
with open("conn_info.txt", 'r') as file:
    lines = file.readlines()
    LISTEN_PORT = int(lines[1])
    SEND_PORT = int(lines[2])
    header = struct.Struct(lines[4])
    file.close()
recv_buffer = {}  # socket ---> str
send_buffer = {}  # socket ---> str
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
                Connected_Clients[inSock] = [outSock, "", [False, 1], "@@broadcast@@"]
                                                                # add dynamic room stuff later
                recv_buffer[inSock] = None
                sendStr = Server_Messages[0] + "\n" + Server_Messages[1] + "\n"+ Server_Messages[2]
                send_buffer[outSock] = sendStr
            else: #receive from socket
                try:
                    fullStr = sock.recv(1024)
                    pass
                except socket.error:
                    outSock = Connected_Clients.pop(sock)

                    recv_buffer.pop(sock)
                    print("popping in error catch")
                    send_buffer.pop(outSock[0])
                    outSock[0].close()
                    sock.close()
                    continue

                if recv_buffer[sock]: #data already exists in buffer.
                    recv_buffer[sock][1] += fullStr.decode('ascii')
                    if len(recv_buffer[sock][1]) == recv_buffer[sock][0]:
                        loadSendBuffer(sock)
                    else:
                        print("Message not done")
                    pass
                else: #first part of transmission. get byte size and rest of chunk.
                    sizeOfMessage = header.unpack(fullStr[0:header.size])[0]
                    recv_buffer[sock] = (sizeOfMessage, fullStr[header.size:].decode('ascii'))
                    if len(recv_buffer[sock][1]) == recv_buffer[sock][0]:
                        loadSendBuffer(sock)
                    else:
                        print("Message not done")
                    pass
        for sock in w:
            try:
                if send_buffer[sock]:
                    toSend = send_buffer[sock].encode('ascii')
                    sock.sendall(toSend)
                    send_buffer[sock] = None
                    print(toSend, " sent to ", sock.getpeername())
                    pass
            except KeyError: #socket disconnected and cleaned up. w, not updated though.
                continue
        for sock in e:
            # might never be reached. Leaving it, because I'm paranoid.
            outSock = Connected_Clients.pop(sock)
            recv_buffer.pop(sock)
            print("popping in exceptional case")
            send_buffer.pop(outSock[0])
            outSock[0].close()
            sock.close()
            pass


def noneFilter(array):
    returnList = []
    for elem in array:
        if elem:
            returnList.append(elem)
    return returnList


def createListenSocket():
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

def loadSendBuffer(ID):
    if not Connected_Clients[ID][2][0]: #not yet authenticated.
        if Connected_Clients[ID][2][1] == 0: # send pre-loaded menu screen to user.
            Connected_Clients[ID][2][1] = 1
        elif Connected_Clients[ID][2][1] == 1: #reply should be 0 or 1, send appropriate response.
            try:
                choice = int(recv_buffer[ID][1])
            except ValueError:
                sendStr = Server_Messages[11]  # "Invalid Response"
            else:
                print("Choice = ", choice)
                if not choice in [0, 1]:
                    sendStr = Server_Messages[11]
                else:
                    sendStr = Server_Messages[choice+3] # 3 if 0, 4 if 1.
                    Connected_Clients[ID][2][1] += choice + 1
            send_buffer[Connected_Clients[ID][0]] = sendStr

        elif Connected_Clients[ID][2][1] == 2: #Log in existing user
            # user should be giving us their username
            name = recv_buffer[ID][1]
            with open("users.txt", 'r') as file:
                lines = file.readlines()
                file.close()
            found = False
            for l in lines:
                found = name == l.partition(":")[0]
                if found: break
            del lines
            if found:
                Connected_Clients[ID][2][1] = 4
                Connected_Clients[ID][1] = name
                send_buffer[Connected_Clients[ID][0]] = Server_Messages[5]
            else:
                send_buffer[Connected_Clients[ID][0]] = Server_Messages[8]

        elif Connected_Clients[ID][2][1] == 3: #Create New User
            # user should be giving a new username
            name = recv_buffer[ID][1]
            with open("users.txt", 'r') as file:
                lines = file.readlines()
                file.close()
            found = False
            for l in lines:
                found = name == l.partition(":")[0]
                if found: break
            del lines
            if found:
                send_buffer[Connected_Clients[ID][0]] = Server_Messages[12]
            else:
                Connected_Clients[ID][2][1] = 5
                send_buffer[Connected_Clients[ID][0]] = Server_Messages[13]
                with open("users.txt", 'a') as file:
                    file.write("\n" + name)
                    file.close()
                Connected_Clients[ID][1] = name
        elif Connected_Clients[ID][2][1] == 4: # get existing password
            #security stinks right now, clean up and make it "secure"
            password = recv_buffer[ID][1]
            with open("users.txt", 'r') as file:
                lines = file.readlines()
                file.close()
            fullUser = ()
            for l in lines:
                fullUser = l.partition(":")
                if Connected_Clients[ID][1] == fullUser[0]:
                    break
            del lines
            if password == fullUser[2].replace("\n", ""): #password correct, user fully authenticated.
                send_buffer[Connected_Clients[ID][0]] = Server_Messages[7]
                Connected_Clients[ID][2][0] = True
            else:
                send_buffer[Connected_Clients[ID][0]] = Server_Messages[10] #Add counter later for limited number of attempts.
        elif Connected_Clients[ID][2][1] == 5: #Create a new password.
            password = recv_buffer[ID][1]
            formatPassword = Connected_Clients[ID][1] + ":" + password
            miscellaneous.findAndReplace("users.txt", formatPassword, Connected_Clients[ID][1])
            Connected_Clients[ID][2][1] = 6
            send_buffer[Connected_Clients[ID][0]] = Server_Messages[6]
        elif Connected_Clients[ID][2][1] == 6: #Confirm the new password
            password = recv_buffer[ID][1]
            with open("users.txt", 'r') as file:
                lines = file.readlines()
                file.close()
            fullUser = ()
            for l in lines:
                fullUser = l.partition(":")
                if Connected_Clients[ID][1] == fullUser[0]:
                    break
            del lines
            print("Password = ", password)
            print("checking against = ", fullUser[2].replace("\n", ""))
            if password == fullUser[2].replace("\n", ""): #password matches, user fully authenticated.
                send_buffer[Connected_Clients[ID][0]] = Server_Messages[14] + '\n' + Server_Messages[7]
                Connected_Clients[ID][2][0] = True
            else:
                send_buffer[Connected_Clients[ID][0]] = Server_Messages[15] #Add timeout.
            miscellaneous.cleanNewLines("users.txt")

    else:
        doNext = inputHandler(recv_buffer[ID][1])  # temporary???? Function returns an array.
        if doNext[0] == "message":  # not a command. user is chatting.
            fullText = ":" + Connected_Clients[ID][1] + ": " + doNext[1]
            for outClient in send_buffer:
                send_buffer[outClient] = fullText
            print("Send Buffer: \n ", send_buffer)
    recv_buffer[ID] = None  # empty the buffer. transferred to send buffer


if __name__ == "__main__":
    messageFile = open("Messages.txt", 'r')
    Server_Messages = messageFile.readlines()
    messageFile.close()
    for i in range(0, len(Server_Messages)):
        Server_Messages[i] = Server_Messages[i].replace('\n', '')
    RoomList = Room.LoadRooms()
    listSocket = createListenSocket()
    Connected_Clients[listSocket] = [None, "@@server", [False, 0]]
    try:
        Main(listSocket)
    except ConnectionError as error:
        print("There was a boo-boo: \n", error)
