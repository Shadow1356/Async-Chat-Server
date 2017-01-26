import select, socket, Room, struct,  miscellaneous

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
Rooms = {} #Room.roomName --> Room
user_cache = {} #socketID -> string of cache


def Main(listener):
    Broadcast = Rooms["@@broadcast@@"]
    while True:  # probably add condition later
        r, w, e = next(selectGenerator())

        for sock in r:
            if sock is listener:  # add new socket
                inSock, address = listener.accept()
                inSock.shutdown(socket.SHUT_WR)
                inSock.setblocking(0.0)
                outSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                outSock.connect((address[0], SEND_PORT))
                #outSock.setblocking(0)
                # while True:
                #     try:
                #         outSock.connect((address[0], SEND_PORT))
                #     except BlockingIOError:
                #         continue
                #     else:
                #         break
                ###Since recv_sock is not blocking in __output, outSock should be okay.
                Connected_Clients[inSock] = [outSock, "", [False, 1], []]
                recv_buffer[inSock] = None
                sendStr = Server_Messages[0] + "\n" + Server_Messages[1] + "\n"+ Server_Messages[2]
                send_buffer[outSock] = sendStr
                user_cache[inSock] = {} # for the command processing generator.
            else: #receive from socket
                try:
                    fullStr = sock.recv(1024) #possible timeout error.
                    if recv_buffer[sock]:  # data already exists in buffer.
                        recv_buffer[sock][1] += fullStr.decode('ascii')
                        if len(recv_buffer[sock][1]) == recv_buffer[sock][0]:
                            loadSendBuffer(sock)
                        else:
                            print("Message not done")
                    else:  # first part of transmission. get byte size and rest of chunk.
                        print("MESSAGE = ", fullStr)
                        sizeOfMessage = header.unpack(fullStr[0:header.size])[0]
                        recv_buffer[sock] = (sizeOfMessage, fullStr[header.size:].decode('ascii'))
                        if len(recv_buffer[sock][1]) == recv_buffer[sock][0]:
                            loadSendBuffer(sock)
                        else:
                            print("Message not done")
                except (socket.error, struct.error) as error:
                    outSock = Connected_Clients.pop(sock)
                    try:
                        del user_cache[sock]
                    except KeyError:
                        pass  # user not logged in and cache not created yet.
                    print("error was: ", error)
                    print(sock)
                    recv_buffer.pop(sock)
                    print("popping in error catch")
                    send_buffer.pop(outSock[0])
                    outSock[0].close()
                    sock.close()
                    continue

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
            try:
                del user_cache[sock]
            except KeyError:
                pass #user not logged in and cache not created yet.
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
    contentArray = recv_buffer[ID][1].split(":`:")
    if not Connected_Clients[ID][2][0]: #not yet authenticated.
        if Connected_Clients[ID][2][1] == 0: # send pre-loaded menu screen to user.
            Connected_Clients[ID][2][1] = 1
        elif Connected_Clients[ID][2][1] == 1: #reply should be 0 or 1, send appropriate response.
            try:
                choice = int(contentArray[0])
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
            name = contentArray[0]
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
            name = contentArray[0]
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
            password = contentArray[0]
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
                for room in Rooms: #Load the rooms that the user is in.
                    if Connected_Clients[ID][1] in Rooms[room].Members:
                        print(Rooms[room])
                        Connected_Clients[ID][3].append(Rooms[room])
            else:
                send_buffer[Connected_Clients[ID][0]] = Server_Messages[10] #Add counter later for limited number of attempts.
        elif Connected_Clients[ID][2][1] == 5: #Create a new password.
            password = contentArray[0]
            formatPassword = Connected_Clients[ID][1] + ":" + password
            miscellaneous.findAndReplace("users.txt", formatPassword, Connected_Clients[ID][1])
            Connected_Clients[ID][2][1] = 6
            send_buffer[Connected_Clients[ID][0]] = Server_Messages[6]
        elif Connected_Clients[ID][2][1] == 6: #Confirm the new password
            password = contentArray[0]
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

                Connected_Clients[ID][3][0].addMember(Connected_Clients[ID][1], "@@server")
            else:
                send_buffer[Connected_Clients[ID][0]] = Server_Messages[15] #Add timeout.
            miscellaneous.cleanNewLines("users.txt")

    else:
        if not contentArray[0]: #no message from user. user just changing room or something. REVISIT
            pass #just empty the recv_buffer
        elif contentArray[0][0] == "`": # invoking a new command
            Command = contentArray[0][1:].split(" ")
            keyword = Command[0]
            print("Keyword = ", keyword)
            args = Command[1:]
            print("args = ", args, len(args))
            print("Before: ", Connected_Clients[ID])
            doNext = process_command(keyword, args, ID)
            print("generatorOut : ", doNext)
        elif Connected_Clients[ID][2][1] > 6: #user in a command
            int_to_str = {7: "name",
                          8: "password",
                          9: "new_room",
                          10: "join",
                          11: "see_perm",
                          12: "see_room",
                          13: "whisper",
                          14: "broadcast",
                          15: "see_active"}
            print(contentArray)
            args = contentArray[0].split(" ")
            print(args)
            keyword = int_to_str[Connected_Clients[ID][2][1]]
            doNext = process_command(keyword, args, ID)
            print("generatorOut : ", doNext)
        else: # not a command. user is chatting.
            try: #check if whispering.
                Target = user_cache[ID]["TARGET"]
                fullText = Connected_Clients[ID][1] + "->" \
                           + Connected_Clients[Target][1] + ": " \
                           + contentArray[0]
                if Connected_Clients[Target][2][0]: #check if user validated
                    send_buffer[Connected_Clients[Target][0]] = fullText
                    send_buffer[Connected_Clients[ID][0]] = fullText
                else:
                    send_buffer[Connected_Clients[ID][0]] = Server_Messages[9]
            except KeyError: #not whispering
                #validate room first
                if not contentArray[1] in Rooms: #room doesn't exist
                    send_buffer[Connected_Clients[ID][0]] = Server_Messages[18]
                elif not Connected_Clients[ID][1] in Rooms[contentArray[1]].Members: #user not in room
                    send_buffer[Connected_Clients[ID][0]] = Server_Messages[19]
                else:
                    fullText = contentArray[1] + ":" + Connected_Clients[ID][1] + ": " + contentArray[0]
                    for inClient in Connected_Clients:
                        # check if user is validated and in the room, before sending output.
                        # Remove second check? Checked Above?
                        if Connected_Clients[inClient][2][0] and Rooms[contentArray[1]] in Connected_Clients[inClient][3]:
                            send_buffer[Connected_Clients[inClient][0]] = fullText
            print("Send Buffer: \n ", send_buffer)
    recv_buffer[ID] = None  # empty the buffer. transferred to send buffer

def process_command(keyword, args, ID):
    global user_cache
    keyword = keyword.lower().strip()
    str_to_int = {"name": 7,
                  "password": 8,
                  "new_room": 9,
                  "join": 10,
                  "see_perm":11,
                  "see_room":12,
                  "whisper": 13,
                  "broadcast": 14,
                  "see_active": 15}

    try:
        control = str_to_int[keyword]
    except KeyError:
        send_buffer[Connected_Clients[ID][0]] = Server_Messages[30]
        Connected_Clients[ID][2][1] = -2 # not continuing.
        return True
    if keyword == "name":
        if len(args) == 0:
            send_buffer[Connected_Clients[ID][0]] = Server_Messages[4]
            Connected_Clients[ID][2][1] = control #7
            return False
        with open("users.txt", 'r') as file:
            lines = file.readlines()
            file.close()
        found = False
        currentUser = ()
        for l in lines:
            fullUser = l.partition(":")
            found = args[0] == fullUser[0]
            if fullUser[0] == Connected_Clients[ID][1]:
                currentUser = fullUser
            if found: break
        del lines, fullUser
        if found:
            del currentUser
            Connected_Clients[ID][2][1] = control
            send_buffer[Connected_Clients[ID][0]] = Server_Messages[12]
            return False
        else:
            toSend = Server_Messages[16] + " " + args[0]
            currentUser_str = currentUser[0] + currentUser[1] + currentUser[2].replace("\n", '')
            newUser_str = args[0] + currentUser[1] + currentUser[2].replace("\n", '')
            print(currentUser_str)
            print(newUser_str)
            for room in Connected_Clients[ID][3]:
               # print(room)
                room.changeUser(Connected_Clients[ID][1], args[0])
            miscellaneous.findAndReplace("users.txt", newUser_str, currentUser_str)
            del currentUser, newUser_str, currentUser_str
            Connected_Clients[ID][1] = args[0]
            send_buffer[Connected_Clients[ID][0]] = toSend
            Connected_Clients[ID][2][1] = -1 #denotes done in function successfully
            return True
    elif keyword == "password": #Add security/Multistep password Reset later
        if len(args) == 0:
            send_buffer[Connected_Clients[ID][0]] = Server_Messages[13]
            Connected_Clients[ID][2][1] = control
            return False
        # change the user's password
        with open("users.txt", 'r') as file:
            lines = file.readlines()
            file.close()
        currentUser = ()
        for l in lines:
            fullUser = l.partition(":")
            if fullUser[0] == Connected_Clients[ID][1]:
                currentUser = fullUser
                break
        del lines, fullUser
        currentUser_str = currentUser[0] + currentUser[1] + currentUser[2].replace("\n", '')
        newUser_str = currentUser[0] + currentUser[1] + args[0]
        print(currentUser_str)
        print(newUser_str)
        miscellaneous.findAndReplace("users.txt", newUser_str, currentUser_str)
        del currentUser, newUser_str, currentUser_str
        send_buffer[Connected_Clients[ID][0]] = Server_Messages[17]
        Connected_Clients[ID][2][1] = -1 #successfully done with function
        return True
    elif keyword == "new_room": # do invite lists later
        try:
            print("Name Cache: ", user_cache[ID]["NAME"])
        except KeyError:
            user_cache[ID]["NAME"] = ""
        try:
            print("Permissions Cache: ", user_cache[ID]["PERM"])
        except KeyError:
            user_cache[ID]["PERM"] = ""
        for a in args:#Make idiot-proof later
            if (a.lower() == "public" or a.lower() == "private") and not user_cache[ID]["PERM"]:
                user_cache[ID]["PERM"] = a.lower()
            elif a[0] == "[":
                newStr = a.replace("[", "")
                newStr = newStr.replace("]", "")
                user_cache[ID]["INVITES"] = newStr
            elif not user_cache[ID]["NAME"]:
                user_cache[ID]["NAME"] = a
        if not user_cache[ID]["PERM"]:
            send_buffer[Connected_Clients[ID][0]] = Server_Messages[22]
            Connected_Clients[ID][2][1] = control
            return False
        if not user_cache[ID]["NAME"]:
            send_buffer[Connected_Clients[ID][0]] = Server_Messages[21]
            Connected_Clients[ID][2][1] = control
            return False
        # Try to make the room
        try:
            perm_dict = {"private": False, "public": True} # values already .lower()ed
            newRoom = Room.Room(user_cache[ID]["NAME"], perm_dict[user_cache[ID]["PERM"]], Connected_Clients[ID][1], False)
        except FileExistsError:
            user_cache[ID]["NAME"] = ""
            send_buffer[Connected_Clients[ID][0]] = Server_Messages[23]
            Connected_Clients[ID][2][1] = control
            return False
        else:
            Rooms[newRoom.roomName] = newRoom
            Connected_Clients[ID][3].append(newRoom)
            send_buffer[Connected_Clients[ID][0]] = Server_Messages[24]
            Connected_Clients[ID][2][1] = -1 # done
            del user_cache[ID]["NAME"], user_cache[ID]["PERM"] #Add invites later
            return True
    elif keyword == "join":
        if len(args) == 0:
            send_buffer[Connected_Clients[ID][0]] = Server_Messages[21]
            Connected_Clients[ID][2][1] = control
            return False
        if not args[0] in Rooms:
            send_buffer[Connected_Clients[ID][0]] = Server_Messages[18]
            Connected_Clients[ID][2][1] = -2 #function will not be continuing
            return True
        if Rooms[args[0]] in Connected_Clients[ID][3]: # user already in room
            send_buffer[Connected_Clients[ID][0]] = Server_Messages[31]
            Connected_Clients[ID][2][1] = -2 # not continuing
            return True
        try:
            Rooms[args[0]].addMember(Connected_Clients[ID][1], Connected_Clients[ID][1])
        except PermissionError: #Room is private.
            send_buffer[Connected_Clients[ID][0]] = Server_Messages[20]
            Connected_Clients[ID][2][1] = -2 #Function will not continue executing.
            return True
        else:
            Connected_Clients[ID][3].append(Rooms[args[0]])
            message = Server_Messages[25] + " " + args[0]
            send_buffer[Connected_Clients[ID][0]] = message
            Connected_Clients[ID][2][1] = -1 #function executed successfully.
            return True
    elif keyword == "see_perm":
        if len(args) == 0:
            send_buffer[Connected_Clients[ID][0]] = Server_Messages[21]
            Connected_Clients[ID][2][1] = control
            return False
        if not args[0] in Rooms:
            send_buffer[Connected_Clients[ID][0]] = Server_Messages[18]
            Connected_Clients[ID][2][1] = -2 #Function will not continue
            return True
        admin_list =[]
        member_list = []
        toSend = ""
        if Rooms[args[0]].isPublic:
            toSend += ("Public Room: " + args[0] + "\n")
        else:
            toSend += ("Private Room: " + args[0] + "\n")
        for user in Rooms[args[0]].Members:
            if user == Rooms[args[0]].owner:
                toSend += ("Owner:\n\t" + user+"\n")
            elif user in Rooms[args[0]].Admins:
                admin_list.append(user)
            else:
                member_list.append(user)
        toSend += "Admins:\n"
        for user in admin_list:
            toSend += ("\t" + user+"\n")
        toSend += "Members:\n"
        for user in member_list:
            toSend += ("\t" +user+"\n")
        send_buffer[Connected_Clients[ID][0]] = toSend
        Connected_Clients[ID][2][1] = -1 # Function Completed Successfully.
        return True
    elif keyword == "see_room":
        if len(args) == 0:
            send_buffer[Connected_Clients[ID][0]] = Server_Messages[21]
            Connected_Clients[ID][2][1] = control
            return False
        if not args[0] in Rooms:
            send_buffer[Connected_Clients[ID][0]] = Server_Messages[18]
            Connected_Clients[ID][2][1] = -2 #Function will not continue
            return True
        toSend = ""
        if Rooms[args[0]].isPublic:
            toSend += ("\tPublic Room: " + args[0] + "\n")
        else:
            toSend += ("\tPrivate Room: " + args[0] + "\n")
        tabCount = 0 # 4 users, then next line
        for user in Rooms[args[0]].Members:
            toSend += (user + "\t")
            tabCount += 1
            if tabCount == 3:
                toSend += "\n"
        send_buffer[Connected_Clients[ID][0]] = toSend
        Connected_Clients[ID][2][1] = -1 # Function Completed Successfully.
        return True
    elif keyword == "whisper":
        if len(args) == 0:
            send_buffer[Connected_Clients[ID][0]] = Server_Messages[4]
            Connected_Clients[ID][2][1] = control
            return False
        user_cache[ID]["TARGET"] = None
        for sock_id in Connected_Clients:
            if Connected_Clients[sock_id][1] == args[0]:
                user_cache[ID]["TARGET"] = sock_id
                break
        if not user_cache[ID]["TARGET"]:
            send_buffer[Connected_Clients[ID][0]] = Server_Messages[8]
            Connected_Clients[ID][2][1] = -2 #function will not continue
            return True
        message = Server_Messages[27] + args[0] + Server_Messages[28]
        send_buffer[Connected_Clients[ID][0]] = message
        Connected_Clients[ID][2][1] = -1 #Executed Successfully.
        return True
    elif keyword == "broadcast":
        try:
            del user_cache[ID]["TARGET"]
        except KeyError:
            send_buffer[Connected_Clients[ID][0]] = Server_Messages[26]
            Connected_Clients[ID][2][1] = -1 #Executed Successfully
            return True
        else:
            message = Server_Messages[29] + Server_Messages[28]
            send_buffer[Connected_Clients[ID][0]] = message
            Connected_Clients[ID][2][1] = -1 #Executed Successfully
            return True
    elif keyword == "see_active":
        if len(args) == 0:
            send_buffer[Connected_Clients[ID][0]] = Server_Messages[21]
            Connected_Clients[ID][2][1] = control
            return False
        if not args[0] in Rooms:
            send_buffer[Connected_Clients[ID][0]] = Server_Messages[18]
            Connected_Clients[ID][2][1] = -2 #Function will not continue
            return True
        tempStr = ""
        tabCount = 0 # 4 then newline
        for inClient in Connected_Clients: # check each connected client
            print("RoomArray: ", Connected_Clients[inClient])
            try:
                if Rooms[args[0]] in Connected_Clients[inClient][3]:
                    tempStr += (Connected_Clients[inClient][1] + "\t")
                    tabCount+= 1
                    if tabCount == 3:
                        tempStr += "\n"
                        tabCount = 0
            except IndexError: #inclient is Server and is not in any rooms
                pass
        send_buffer[Connected_Clients[ID][0]] = tempStr
        Connected_Clients[ID][2][1] = control
        return True

if __name__ == "__main__":
    messageFile = open("Messages.txt", 'r')
    Server_Messages = messageFile.readlines()
    messageFile.close()
    for i in range(0, len(Server_Messages)):
        Server_Messages[i] = Server_Messages[i].replace('\n', '')
    Rooms = Room.LoadRooms()
    listSocket = createListenSocket()
    Connected_Clients[listSocket] = [None, "@@server", [False, 0]]
    try:
        Main(listSocket)
    except ConnectionError as error:
        print("There was a boo-boo: \n", error)
    except KeyboardInterrupt:
        #Shutdown Server correctly.....later
        print("Server stopped.")
