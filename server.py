import select, socket, Room, struct,  miscellaneous, Logger
from copy import deepcopy
from time import strftime
"""
Globals
"""
with open("conn_info.txt", 'r') as file:
    lines = file.readlines()
    LISTEN_PORT = int(lines[1])
    SEND_PORT = int(lines[2])
    header = struct.Struct(lines[3])
    file.close()
recv_buffer = {}  # socket ---> str
send_buffer = {}  # socket ---> str
Server_Messages = []
Connected_Clients = {}  # socket ---> [socket, str]
Rooms = {} #Room.roomName --> Room
user_cache = {} #socketID -> string of cache


def Main(listener):
    global log, recv_buffer, send_buffer, Server_Messages, Connected_Clients, Rooms, user_cache
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
                send_buffer[outSock] = formatMessage(Server_Messages[0], "Q",
                                                     ["Log in", "Create New Account"])
                user_cache[inSock] = {} # for the command processing generator.
            else: #receive from socket
                try:
                    fullStr = sock.recv(1024) #possible timeout error.
                    if recv_buffer[sock]:  # data already exists in buffer.
                        recv_buffer[sock][1] += fullStr.decode('ascii')
                        if len(recv_buffer[sock][1]) == recv_buffer[sock][0]:
                            loadSendBuffer(sock)
                        else:
                            log.debug("Message not done")
                    else:  # first part of transmission. get byte size and rest of chunk.
                        log.debug("MESSAGE = ", fullStr)
                        sizeOfMessage = header.unpack(fullStr[0:header.size])[0]
                        recv_buffer[sock] = (sizeOfMessage, fullStr[header.size:].decode('ascii'))
                        if len(recv_buffer[sock][1]) == recv_buffer[sock][0]:
                            loadSendBuffer(sock)
                        else:
                            log.debug("Message not done")
                except (socket.error, struct.error) as error:
                    outSock = Connected_Clients.pop(sock)
                    try:
                        del user_cache[sock]
                    except KeyError:
                        pass  # user not logged in and cache not created yet.
                    log.debug("error was: ", error)
                    log.debug(sock)
                    recv_buffer.pop(sock)
                    log.debug("popping in error catch")
                    send_buffer.pop(outSock[0])
                    outSock[0].close()
                    sock.close()
                    continue

        for sock in w:
            try:
                if send_buffer[sock]:
                    message_toSend = send_buffer[sock].encode('ascii')
                    toSend = header.pack(len(message_toSend)) + message_toSend
                    sock.sendall(toSend)
                    send_buffer[sock] = None
                    log.debug(toSend, " sent to ", sock.getpeername())
            except KeyError: #socket disconnected and cleaned up. w, not updated though.
                continue
            try:
            # Going to retry an operation
             #Add Timeout later.
                log.debug("User Retry Cache = ", user_cache[sock]["RETRY"])
            except KeyError:
                pass
               # log.debug("User Retry Cache is non-existant")
                #printing  ^that floods the logs
            else:
                recv_buffer[sock][1] = ""
                loadSendBuffer(sock)
        for sock in e:
            # might never be reached. Leaving it, because I'm paranoid.
            outSock = Connected_Clients.pop(sock)
            try:
                del user_cache[sock]
            except KeyError:
                pass #user not logged in and cache not created yet.
            recv_buffer.pop(sock)
            log.debug("popping in exceptional case")
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
    global Connected_Clients
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
    global log, recv_buffer, send_buffer, Server_Messages, Connected_Clients, Rooms, user_cache
    contentArray = recv_buffer[ID][1].split(":`:")
    if not Connected_Clients[ID][2][0]: #not yet authenticated.
        if Connected_Clients[ID][2][1] == 0: # send pre-loaded menu screen to user.
            Connected_Clients[ID][2][1] = 1
        elif Connected_Clients[ID][2][1] == 1: #reply should be 0 or 1, send appropriate response.
            try:
                choice = int(contentArray[0])
            except ValueError:
                sendStr = formatMessage(Server_Messages[11], "E")  # "Invalid Response"
            else:
                log.debug("Choice = ", choice)
                if not choice in [0, 1]:
                    sendStr = formatMessage(Server_Messages[11], "E")
                else:
                    sendStr = formatMessage(Server_Messages[choice+3], "M") # 3 if 0, 4 if 1.
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
                unique_check = findClient(name)
                log.debug("Unique Check: ", unique_check)
                if unique_check[0]:
                    send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[54], "Q",
                                                                          ["Log in", "Create New User"])
                    Connected_Clients[ID][2][1] = 1
                else:
                    Connected_Clients[ID][2][1] = 4
                    Connected_Clients[ID][1] = name
                    send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[5], "M")
            else:
                send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[8], "E")

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
                send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[12], "E")
            else:
                Connected_Clients[ID][2][1] = 5
                send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[13], "M")
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
                send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[7], "M")
                Connected_Clients[ID][2][0] = True
                Connected_Clients[ID][2][1] = -1
                for room in Rooms: #Load the rooms that the user is in.
                    if Connected_Clients[ID][1] in Rooms[room].Members:
                        log.debug(Rooms[room])
                        Connected_Clients[ID][3].append(Rooms[room])
            else:
                send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[10], "E") #Add counter later for limited number of attempts.
        elif Connected_Clients[ID][2][1] == 5: #Create a new password.
            password = contentArray[0]
            formatPassword = Connected_Clients[ID][1] + ":" + password
            miscellaneous.findAndReplace("users.txt", formatPassword, Connected_Clients[ID][1])
            Connected_Clients[ID][2][1] = 6
            send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[6], "M")
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
            log.debug("Password = ", password)
            log.debug("checking against = ", fullUser[2].replace("\n", ""))
            if password == fullUser[2].replace("\n", ""): #password matches, user fully authenticated.
                msg = Server_Messages[14] + '\n' + Server_Messages[7]
                send_buffer[Connected_Clients[ID][0]] = formatMessage(msg, "M")
                Connected_Clients[ID][2][0] = True
                Connected_Clients[ID][2][1] = -1
                Connected_Clients[ID][3].append(Rooms["@@broadcast@@"])
                Connected_Clients[ID][3][0].addMember(Connected_Clients[ID][1], "@@server")
            else:
                send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[15], "E") #Add timeout.
            miscellaneous.cleanNewLines("users.txt")

    else:
        if not contentArray[0]: #no message from user. user just changing room or something. REVISIT
            pass #just empty the recv_buffer
        elif contentArray[0][0] == "`": # invoking a new command
            Command = contentArray[0][1:].split(" ")
            keyword = Command[0]
            log.debug("Keyword = ", keyword)
            args = Command[1:]
            log.debug("args = ", args, len(args))
            log.debug("Before: ", Connected_Clients[ID])
            doNext = process_command(keyword, args, ID)
            log.debug("generatorOut : ", doNext)
        elif Connected_Clients[ID][2][1] > 6: #user in a command
            int_to_str = {7: "name",
                          8: "password",
                          9: "new_room",
                          10: "join",
                          11: "see_perm",
                          12: "see_room",
                          13: "whisper",
                          14: "broadcast",
                          15: "see_active",
                          16: "invite",
                          17: "leave",
                          18: "make_owner",
                          19: "log_out",
                          20: "delete_account"}
            log.debug(contentArray)
            args = contentArray[0].split(" ")
            log.debug(args)
            keyword = int_to_str[Connected_Clients[ID][2][1]]
            doNext = process_command(keyword, args, ID)
            log.debug("generatorOut : ", doNext)
        else: # not a command. user is chatting.
            try: #check if whispering.
                Target = user_cache[ID]["TARGET"]
                fullText = Connected_Clients[ID][1] + "->" \
                           + Connected_Clients[Target][1] + ": " \
                           + contentArray[0]
                if Connected_Clients[Target][2][0]: #check if user validated
                    color = getColor(Connected_Clients[ID][1])
                    toWhisper = formatMessage(fullText, "W", [color])
                    send_buffer[Connected_Clients[Target][0]] = toWhisper
                    send_buffer[Connected_Clients[ID][0]] = toWhisper
                else:
                    send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[34], "E")
            except KeyError: #not whispering
                #validate room first
                if not contentArray[1] in Rooms: #room doesn't exist
                    send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[18],"E")
                elif not Connected_Clients[ID][1] in Rooms[contentArray[1]].Members: #user not in room
                    send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[19], "E")
                else:
                    text = contentArray[1] + ":" + Connected_Clients[ID][1] + ": " + contentArray[0]
                    add_args = [getColor(Connected_Clients[ID][1]), getColor(contentArray[1])]
                    fullText = formatMessage(text, "C", add_args)
                    for inClient in Connected_Clients:
                        # check if user is validated and in the room, before sending output.
                        # Remove second check? Checked Above?
                        if Connected_Clients[inClient][2][0] and Rooms[contentArray[1]] in Connected_Clients[inClient][3]:
                            send_buffer[Connected_Clients[inClient][0]] = fullText
            log.debug("Send Buffer: \n ", send_buffer) #<---Could prove costly, probably remove or change.

    recv_buffer[ID] = None  # empty the buffer. transferred to send buffer

def process_command(keyword, args, ID):
    global user_cache, Connected_Clients, Server_Messages, log, send_buffer, Rooms
    keyword = keyword.lower().strip()
    str_to_int = {"name": 7,
                  "password": 8,
                  "new_room": 9,
                  "join": 10,
                  "see_perm":11,
                  "see_room":12,
                  "whisper": 13,
                  "broadcast": 14,
                  "see_active": 15,
                  "invite": 16,
                  "leave":  17,
                  "make_owner": 18,
                  "log_out": 19,
                  "delete_account": 20}

    try:
        control = str_to_int[keyword]
    except KeyError:
        send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[30], "E")
        Connected_Clients[ID][2][1] = -2 # not continuing.
        return True
    if keyword == "name":
        if len(args) == 0:
            send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[4], "M")
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
            send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[12], "E")
            return False
        else:
            toSend = Server_Messages[16] + " " + args[0]
            currentUser_str = currentUser[0] + currentUser[1] + currentUser[2].replace("\n", '')
            newUser_str = args[0] + currentUser[1] + currentUser[2].replace("\n", '')
            log.debug(currentUser_str)
            log.debug(newUser_str)
            for room in Connected_Clients[ID][3]:
               # print(room)
                room.changeUser(Connected_Clients[ID][1], args[0])
            miscellaneous.findAndReplace("users.txt", newUser_str, currentUser_str)
            del currentUser, newUser_str, currentUser_str
            Connected_Clients[ID][1] = args[0]
            send_buffer[Connected_Clients[ID][0]] = formatMessage(toSend, "M")
            Connected_Clients[ID][2][1] = -1 #denotes done in function successfully
            return True
    elif keyword == "password": #Add security/Multistep password Reset later
        if len(args) == 0:
            send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[13], "M")
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
        log.debug(currentUser_str)
        log.debug(newUser_str)
        miscellaneous.findAndReplace("users.txt", newUser_str, currentUser_str)
        del currentUser, newUser_str, currentUser_str
        send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[17], "M")
        Connected_Clients[ID][2][1] = -1 #successfully done with function
        return True
    elif keyword == "new_room": # do invite lists later
        try:
            log.debug("Name Cache: ", user_cache[ID]["NAME"])
        except KeyError:
            user_cache[ID]["NAME"] = ""
        try:
            log.debug("Permissions Cache: ", user_cache[ID]["PERM"])
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
            send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[22], "Q",
                                                                  ["Public", "Private"])
            Connected_Clients[ID][2][1] = control
            return False
        if not user_cache[ID]["NAME"]:
            send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[21], "M")
            Connected_Clients[ID][2][1] = control
            return False
        # Try to make the room
        try:
            perm_dict = {"private": False, "public": True} # values already .lower()ed
            newRoom = Room.Room(user_cache[ID]["NAME"], perm_dict[user_cache[ID]["PERM"]], Connected_Clients[ID][1], False)
        except FileExistsError:
            user_cache[ID]["NAME"] = ""
            send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[23], "E")
            Connected_Clients[ID][2][1] = control
            return False
        else:
            Rooms[newRoom.roomName] = newRoom
            Connected_Clients[ID][3].append(newRoom)
            send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[24], "M")
            Connected_Clients[ID][2][1] = -1 # done
            del user_cache[ID]["NAME"], user_cache[ID]["PERM"] #Add invites later
            return True
    elif keyword == "join":
        try:
            log.debug(user_cache[ID]["INVITATION"])
        except KeyError:
            pass
        else: #USer has a pending invitation
            requester = findClient(user_cache[ID]["INVITATION"][1])
            if len(args) == 0:
                send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[11], "E")
                Connected_Clients[ID][2][1] = control
                return False
            if args[0] == "y": #user will be joining
                target_room = user_cache[ID]["INVITATION"][0]
                try:
                    Rooms[target_room].addMember(Connected_Clients[ID][1],
                                                 user_cache[ID]["INVITATION"][1])
                except PermissionError:  # Requester does not have the privilege to invite.
                    send_buffer[Connected_Clients[requester[1]][0]] = formatMessage(Server_Messages[40], "E")
                    send_back = formatMessage(user_cache[ID]["INVITATION"][1] + Server_Messages[39], "E")
                    send_buffer[Connected_Clients[ID][0]] = send_back
                    Connected_Clients[ID][2][1] = -2  # Function will not continue executing.
                    del user_cache[ID]["INVITATION"]
                    return True
                else:
                    send_buffer[Connected_Clients[requester[1]][0]] = formatMessage(Server_Messages[41], "M")
                    Connected_Clients[ID][3].append(Rooms[target_room])
                    message = Server_Messages[25] + " " + target_room
                    send_buffer[Connected_Clients[ID][0]] = formatMessage(message, "M")
                    Connected_Clients[ID][2][1] = -1  # function executed successfully.
                    del user_cache[ID]["INVITATION"]
                    return True
            elif args[0] == "n":
                dec_message = formatMessage(Server_Messages[42], "M")
                send_buffer[Connected_Clients[requester[1]][0]] = dec_message
                send_buffer[Connected_Clients[ID][0]] = dec_message
                Connected_Clients[ID][2][1] = -1
                del user_cache[ID]["INVITATION"]
                return True
            else:
                send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[11], "E")
                Connected_Clients[ID][2][1] = control
                return False

        if len(args) == 0:
            room_options = [r.roomName for r in Connected_Clients[ID][3]]
            send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[21], "Q",
                                                                  room_options)
            Connected_Clients[ID][2][1] = control
            return False
        if not args[0] in Rooms:
            send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[18], "E")
            Connected_Clients[ID][2][1] = -2 #function will not be continuing
            return True
        if Rooms[args[0]] in Connected_Clients[ID][3]: # user already in room
            send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[31], "M")
            Connected_Clients[ID][2][1] = -2 # not continuing
            return True
        try:
            Rooms[args[0]].addMember(Connected_Clients[ID][1], Connected_Clients[ID][1])
        except PermissionError: #Room is private.
            send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[20], "E")
            Connected_Clients[ID][2][1] = -2 #Function will not continue executing.
            return True
        else:
            Connected_Clients[ID][3].append(Rooms[args[0]])
            message = Server_Messages[25] + " " + args[0]
            send_buffer[Connected_Clients[ID][0]] = formatMessage(message, "M")
            Connected_Clients[ID][2][1] = -1 #function executed successfully.
            return True
    elif keyword == "see_perm":
        if len(args) == 0:
            room_options = [r.roomName for r in Connected_Clients[ID][3]]
            send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[21], "Q",
                                                                  room_options)
            Connected_Clients[ID][2][1] = control
            return False
        if not args[0] in Rooms:
            send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[18], "E")
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
        send_buffer[Connected_Clients[ID][0]] = formatMessage(toSend, "M")
        Connected_Clients[ID][2][1] = -1 # Function Completed Successfully.
        return True
    elif keyword == "see_room":
        if len(args) == 0:
            room_options = [r.roomName for r in Connected_Clients[ID][3]]
            send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[21], "Q",
                                                                  room_options)
            Connected_Clients[ID][2][1] = control
            return False
        if not args[0] in Rooms:
            send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[18], "E")
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
        send_buffer[Connected_Clients[ID][0]] = formatMessage(toSend, "M")
        Connected_Clients[ID][2][1] = -1 # Function Completed Successfully.
        return True
    elif keyword == "whisper":
        if len(args) == 0:
            send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[4], "M")
            Connected_Clients[ID][2][1] = control
            return False
        user_cache[ID]["TARGET"] = None
        for sock_id in Connected_Clients:
            if Connected_Clients[sock_id][1] == args[0]:
                user_cache[ID]["TARGET"] = sock_id
                break
        if not user_cache[ID]["TARGET"]:
            send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[8], "E")
            Connected_Clients[ID][2][1] = -2 #function will not continue
            return True
        message = Server_Messages[27] + args[0] + Server_Messages[28]
        send_buffer[Connected_Clients[ID][0]] = formatMessage(message, "M")
        Connected_Clients[ID][2][1] = -1 #Executed Successfully.
        return True
    elif keyword == "broadcast":
        try:
            del user_cache[ID]["TARGET"]
        except KeyError:
            send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[26], "E")
            Connected_Clients[ID][2][1] = -1 #Executed Successfully
            return True
        else:
            message = Server_Messages[29] + Server_Messages[28]
            send_buffer[Connected_Clients[ID][0]] = formatMessage(message, "M")
            Connected_Clients[ID][2][1] = -1 #Executed Successfully
            return True
    elif keyword == "see_active":
        if len(args) == 0:
            room_options = [r.roomName for r in Connected_Clients[ID][3]]
            send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[21], "Q",
                                                                  room_options)
            Connected_Clients[ID][2][1] = control
            return False
        if not args[0] in Rooms:
            send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[18], "E")
            Connected_Clients[ID][2][1] = -2 #Function will not continue
            return True
        tempStr = ""
        tabCount = 0 # 4 then newline
        for inClient in Connected_Clients: # check each connected client
            log.debug("RoomArray: ", Connected_Clients[inClient])
            try:
                if Rooms[args[0]] in Connected_Clients[inClient][3]:
                    tempStr += (Connected_Clients[inClient][1] + "\t")
                    tabCount+= 1
                    if tabCount == 3:
                        tempStr += "\n"
                        tabCount = 0
            except IndexError: #inclient is Server and is not in any rooms
                pass
        send_buffer[Connected_Clients[ID][0]] = formatMessage(tempStr, "M")
        Connected_Clients[ID][2][1] = control
        return True
    elif keyword == "invite":
        try:
            log.debug(user_cache[ID]["INVITE"])
        except KeyError:
            user_cache[ID]["INVITE"] = ""
        try:
            log.debug(user_cache[ID]["ROOM"])
        except KeyError:
            user_cache[ID]["ROOM"] = ""
        if len(args) == 0:
            Connected_Clients[ID][2][1] = control
            send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[32], "M")
            return False
        if len(args) == 1 and user_cache[ID]["INVITE"]:
            if args[0] in Rooms:
                user_cache[ID]["ROOM"] = args[0]
            else:
                send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[18], "E")
                Connected_Clients[ID][2][1] = control
                return False
        elif len(args) == 1 and user_cache[ID]["ROOM"]:
            search_results = findClient(args[0])
            if not search_results[0]:
                send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[8], "E")
                Connected_Clients[ID][2][1] = control
                return False
            user_cache[ID]["INVITE"] = (args[0], search_results[1])
        elif len(args) == 1:
            at_least_1 = False
            if args[0] in Rooms:
                user_cache[ID]["ROOM"] = args[0]
                at_least_1 = True
            else:
                search_results = findClient(args[0])
                if search_results[0]:
                    user_cache[ID]["INVITE"] = (args[0], search_results[1])
                    at_least_1 = True
            if not at_least_1:
                send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[33], "E")
                Connected_Clients[ID][2][1] = -2 #Function not continuing
                del user_cache[ID]["ROOM"], user_cache[ID]["INVITE"]
        if len(args) > 1:
            for argument in args:
                if argument in Rooms:
                    user_cache[ID]["ROOM"] = argument
                else:
                    search_results = findClient(argument)
                    if search_results[0]:
                        user_cache[ID]["INVITE"] = (argument, search_results[1])
        if user_cache[ID]["INVITE"] and user_cache[ID]["ROOM"]:
            inv_ID = user_cache[ID]["INVITE"][1]
            inv_room = user_cache[ID]["ROOM"]
            inv_name = user_cache[ID]["INVITE"][0]
            if Rooms[inv_room] in Connected_Clients[inv_ID][3]:
                del user_cache[ID]["ROOM"], user_cache[ID]["INVITE"]
                Connected_Clients[ID][2][1] = -2 # function not continuing
                send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[31], "E")
                return True
            if not Connected_Clients[inv_ID][2][0]:
                del user_cache[ID]["ROOM"], user_cache[ID]["INVITE"]
                Connected_Clients[ID][2][1] = -2 #not continuing
                send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[34], "E")
                return True
            if Connected_Clients[inv_ID][2][1] >0:
                # Invitee is doing a command. Wait to send request
                Connected_Clients[ID][2][1] = control
                send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[35], "M")
                user_cache[ID]["RETRY"] = True
                return False
            else:
                inviteMessage = Connected_Clients[ID][1] + Server_Messages[36] \
                            + inv_room + "\n" + Server_Messages[37]
                senderMessage = Server_Messages[38] + inv_name + Server_Messages[28]
                send_buffer[Connected_Clients[inv_ID][0]] = formatMessage(inviteMessage, "Q",
                                                                          ["Accept", "Decline"])
                send_buffer[Connected_Clients[ID][0]] =formatMessage(senderMessage, "M")
                Connected_Clients[ID][2][1] = -1 #FUnction done successfully
                Connected_Clients[inv_ID][2][1] = str_to_int["join"]
                try:
                    del user_cache[ID]["RETRY"]
                except KeyError:
                    pass
                user_cache[inv_ID]["INVITATION"] = (inv_room, Connected_Clients[ID][1])
                del user_cache[ID]["ROOM"], user_cache[ID]["INVITE"]
                return True
        elif not user_cache[ID]["ROOM"]:
            log.debug("IN THE NO ROOM PART")
            room_options = [r.roomName for r in Connected_Clients[ID][3]]
            send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[21], "Q",
                                                                  room_options)
            Connected_Clients[ID][2][1] = control
            return False
        elif not user_cache[ID]["INVITE"]:
            log.debug("INT THE NOT INVITE PART")
            send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[3], "M")
            Connected_Clients[ID][2][1] = control
            return False
    elif keyword == "leave":
        try:
            log.debug(user_cache[ID]["LEAVE"])
        except KeyError:
            user_cache[ID]["LEAVE"] = ""
        if len(args) == 0:
            room_options = [r.roomName for r in Connected_Clients[ID][3]]
            send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[21], "Q",
                                                                  room_options)
            Connected_Clients[ID][2][1] = control
            return False
        if user_cache[ID]["LEAVE"]:
            #args[0] is a the new owner.
            new_owner = findClient(args[0])
            if not new_owner[0]:
                send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[8], "E")
                Connected_Clients[ID][2][1] = -2 #Not continuing
                return True
            user_cache[new_owner[1]]["OFFER"] = (user_cache[ID]["LEAVE"],
                                                 Connected_Clients[ID][1])
            if Connected_Clients[new_owner[1]][2][1] < 0:
                Connected_Clients[new_owner[1]][2][1] = str_to_int["make_owner"]
                Connected_Clients[ID][2][1] = -1 #Done Correctly
                off_message = Server_Messages[48] + Server_Messages[28]
                send_buffer[Connected_Clients[ID][0]] = formatMessage(off_message, "M")
                return True
            else: #User busy Wait to send offer
                Connected_Clients[ID][2][1] = control
                send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[35], "M")
                user_cache[ID]["RETRY"] = True
                return False
        else:
            if not args[0] in Rooms:
                send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[18], "M")
                Connected_Clients[ID][2][1] = -2 #Function will not continue
                return True
            CC_room_index = Connected_Clients[ID][3].index(Rooms[args[0]])
            if len(Rooms[args[0]].Members) == 1:
                #User the only one in the room. Room Being Deleted.
                Rooms[args[0]].deleteRoom(Connected_Clients[ID][1])
                del Rooms[args[0]]
                Connected_Clients[ID][3].pop(CC_room_index)
                send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[45], "M")
                Connected_Clients[ID][2][1] = -1 #Function success
                return True
            if Connected_Clients[ID][1] == Rooms[args[0]].owner:
                #Select a new owner
                send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[46], "M")
                Connected_Clients[ID][2][1] = control
                user_cache[ID]["LEAVE"] = args[0]
                return False
            #Else, delete user from room.
            try:
                Rooms[args[0]].deleteAdmin(Connected_Clients[ID][1], Connected_Clients[ID][1])
            except ValueError:
                pass #User is not necessarily an admin.
            try:
                Rooms[args[0]].deleteMember(Connected_Clients[ID][1], Connected_Clients[ID][1])
            except ValueError: #user is not in the room
                send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[19], "E")
                Connected_Clients[ID][2][1] = -2 #not continuing
                return True
            else:
                Connected_Clients[ID][3].pop(CC_room_index)
                send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[53], "M")
                Connected_Clients[ID][2][1] = -1 #Function success
                return True
    elif keyword == "make_owner":
        try:
            log.debug(user_cache[ID]["OFFER"])
        except KeyError:
            pass
        else: #Someone has offered to make him owner of a room
            requester = findClient(user_cache[ID]["OFFER"][1])
            if len(args) == 0:
                send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[11], "E")
                Connected_Clients[ID][2][1] = control
                return False
            if args[0] == "y":  # user will be new owner
                target_room = user_cache[ID]["OFFER"][0]
                try:
                    Rooms[target_room].setOwner(Connected_Clients[ID][1],
                                                 user_cache[ID]["OFFER"][1])
                except PermissionError:  # Requester is not current owner.
                    send_buffer[Connected_Clients[requester[1]][0]] = formatMessage(Server_Messages[40], "E")
                    perm_error = user_cache[ID]["OFFER"][1] + Server_Messages[39]
                    send_buffer[Connected_Clients[ID][0]] = formatMessage(perm_error, "E")
                    Connected_Clients[ID][2][1] = -2  # Function will not continue executing.
                    del user_cache[ID]["OFFER"]
                    return True
                else:
                    send_buffer[Connected_Clients[requester[1]][0]] = Server_Messages[49]
                    Connected_Clients[ID][3].append(Rooms[target_room])
                    message = Server_Messages[51] + " " + target_room
                    send_buffer[Connected_Clients[ID][0]] = formatMessage(message, "M")
                    Connected_Clients[ID][2][1] = -1  # function executed successfully.
                    del user_cache[ID]["OFFER"]
                    return True
            elif args[0] == "n":
                dec_message = formatMessage(Server_Messages[50], "M")
                send_buffer[Connected_Clients[requester[1]][0]] = dec_message
                send_buffer[Connected_Clients[ID][0]] =dec_message
                Connected_Clients[ID][2][1] = -1
                del user_cache[ID]["OFFER"]
                return True
            else:
                send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[11], "E")
                Connected_Clients[ID][2][1] = control
                return False
        try:
            log.debug(user_cache[ID]["BUYER"])
        except KeyError:
            user_cache[ID]["BUYER"] = ""
        try:
            log.debug(user_cache[ID]["ROOM"])
        except KeyError:
            user_cache[ID]["ROOM"] = ""
        if len(args) == 0:
            Connected_Clients[ID][2][1] = control
            send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[32], "M")
            return False
        if len(args) == 1 and user_cache[ID]["BUYER"]:
            if args[0] in Rooms:
                user_cache[ID]["ROOM"] = args[0]
            else:
                send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[18], "E")
                Connected_Clients[ID][2][1] = control
                return False
        elif len(args) == 1 and user_cache[ID]["ROOM"]:
            search_results = findClient(args[0])
            if not search_results[0]:
                send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[8], "E")
                Connected_Clients[ID][2][1] = control
                return False
            user_cache[ID]["BUYER"] = (args[0], search_results[1])
        elif len(args) == 1:
            at_least_1 = False
            if args[0] in Rooms:
                user_cache[ID]["ROOM"] = args[0]
                at_least_1 = True
            else:
                search_results = findClient(args[0])
                if search_results[0]:
                    user_cache[ID]["BUYER"] = (args[0], search_results[1])
                    at_least_1 = True
            if not at_least_1:
                send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[33], "E")
                Connected_Clients[ID][2][1] = -2  # Function not continuing
                del user_cache[ID]["ROOM"], user_cache[ID]["BUYER"]
        if len(args) > 1:
            for argument in args:
                if argument in Rooms:
                    user_cache[ID]["ROOM"] = argument
                else:
                    search_results = findClient(argument)
                    if search_results[0]:
                        user_cache[ID]["BUYER"] = (argument, search_results[1])
        if user_cache[ID]["BUYER"] and user_cache[ID]["ROOM"]:
            inv_ID = user_cache[ID]["BUYER"][1]
            inv_room = user_cache[ID]["ROOM"]
            inv_name = user_cache[ID]["BUYER"][0]
            if not Connected_Clients[inv_ID][2][0]:
                del user_cache[ID]["ROOM"], user_cache[ID]["BUYER"]
                Connected_Clients[ID][2][1] = -2  # not continuing
                send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[34], "E")
                return True
            if Connected_Clients[inv_ID][2][1] > 0:
                # Invitee is doing a command. Wait to send request
                Connected_Clients[ID][2][1] = control
                send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[35], "M")
                user_cache[ID]["RETRY"] = True
                return False
            else:
                inviteMessage = Connected_Clients[ID][1] + Server_Messages[47] \
                                + inv_room + "\n" + Server_Messages[37]
                senderMessage = Server_Messages[48] + inv_name + Server_Messages[28]
                send_buffer[Connected_Clients[inv_ID][0]] = formatMessage(inviteMessage, "Q",
                                                                          ["Accept", "Decline"])
                send_buffer[Connected_Clients[ID][0]] = formatMessage(senderMessage, "M")
                Connected_Clients[ID][2][1] = -1  # FUnction done successfully
                Connected_Clients[inv_ID][2][1] = control
                try:
                    del user_cache[ID]["RETRY"]
                except KeyError:
                    pass
                user_cache[inv_ID]["OFFER"] = (inv_room, Connected_Clients[ID][1])
                del user_cache[ID]["ROOM"], user_cache[ID]["BUYER"]
                return True
        elif not user_cache[ID]["ROOM"]:
            log.debug("IN THE NO ROOM PART")
            room_options = [r.roomName for r in Connected_Clients[ID][3]]
            send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[21], "Q",
                                                                  room_options)
            Connected_Clients[ID][2][1] = control
            return False
        elif not user_cache[ID]["BUYER"]:
            log.debug("INT THE NOT BUYER PART")
            send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[3], "M")
            Connected_Clients[ID][2][1] = control
            return False
    elif keyword == "log_out":
        #Revert to same state as in beginning upon connection
        #C_C[ID][0] is the same socket
        Connected_Clients[ID][1] = "" #Reset Username
        Connected_Clients[ID][2] = [False, 1] #Not authenticated
        Connected_Clients[ID][3] = [] #Reset active rooms
        recv_buffer[ID] = None
        send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[52], "Q",
                                                              ["Log in", "Create New User"])
        del user_cache[ID]
        return True
    elif keyword == "delete_account":
        #Confirm the the user really wants this.
        try:
            log.debug(user_cache[ID]["DELETE"])
        except KeyError:
            confirm_message = Server_Messages[55] + Server_Messages[56]
            send_buffer[Connected_Clients[ID][0]] = formatMessage(confirm_message, "Q",
                                                                  ["Yes", "No"])
            Connected_Clients[ID][2][1] = control
            user_cache[ID]["DELETE"] = True
        else:
            user_cache[ID]["MASS_DELETE"] = True
            local_copy = deepcopy(Connected_Clients[ID][3])
            for room in local_copy:
                process_command("leave", [room.roomName], ID)
                if Connected_Clients[ID][2][1] == -2:
                    send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[59], "E")
                    return True
            # args[0] should be y/n
            if args[0] == 'y':
                # Erase User from Users.txt
                with open("users.txt", 'r') as file:
                    lines = file.readlines()
                    file.close()
                lineNumber = -1
                for l in lines:
                    fullUser = l.partition(":")
                    if fullUser[0] == Connected_Clients[ID][1]:
                        lineNumber = lines.index(l)
                        break
                del lines, fullUser
                miscellaneous.replaceLine("users.txt", lineNumber + 1, "")
            elif args[0] == 'n':
                del user_cache[ID]["DELETE"], user_cache[ID]["MASS_DELETE"]
                send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[57], "M")
                Connected_Clients[ID][2][1] = -1  # Function Done successfully
                return True
            else:
                send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[11], "E")
                Connected_Clients[ID][2][1] = control
                return False
            Connected_Clients[ID][1] = ""  # Reset Username
            Connected_Clients[ID][2] = [False, 1]  # Not authenticated
            recv_buffer[ID] = None
            send_buffer[Connected_Clients[ID][0]] = formatMessage(Server_Messages[52], "Q",
                                                                  ["Log in", "Create New User"])
            del user_cache[ID]
            return True


def findClient(name):
    global Connected_Clients
    for client, CC in Connected_Clients.items():
        if CC[1] == name:
            return True, client
    return False, None

def formatMessage(text, send_type, additional=[]):
    # formats the message for the client to understand
    # does not encode to ascii or add the header.
    # That ^ is done in main right before sending.
    formatted_string = send_type
    if send_type == "Q":
        options =""
        for option in additional:
            options+= option + ":"
        options += ":"
        formatted_string += options
    elif send_type == "C":
        for i in range(0, 2):
            if len(additional[i]) != 6:
                raise ValueError
            formatted_string+= additional[i]
    elif send_type == "W":
        if len(additional[0]) != 6:
            raise ValueError
        formatted_string += additional[0]
    elif send_type == "M" or send_type == "E":
        pass
    else:
        raise ValueError
    formatted_string += text
    return formatted_string

def getColor(entity): #Terrible variable name; find another.
    # Temporary
    # Use color.txt to get the appropriate color
    # that the user or room has set.
    # entity = Room or Username
    return "FFFFFF"

if __name__ == "__main__":
    logName = "Logs\\"+strftime("%d%m%Y%H%M%S") + ".log"
    log = Logger.Logger(logName)
    messageFile = open("Messages.txt", 'r')
    Server_Messages = messageFile.readlines()
    messageFile.close()
    for i in range(0, len(Server_Messages)):
        Server_Messages[i] = Server_Messages[i].replace('\n', '')
    Rooms = Room.LoadRooms()
    listSocket = createListenSocket()
    Connected_Clients[listSocket] = [None, "@@server", [False, 0]]
    while True:
        try:
            Main(listSocket)
        except ConnectionError as error:
            log.debug("There was a boo-boo: \n", error)
            continue
        except KeyboardInterrupt:
            #Shutdown Server correctly.....later
            log.debug("Server stopped.")
            break
