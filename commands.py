"""
Module for the commands the user can invoke in the chat.
"""
import miscellaneous, Room
messageFile = open("Messages.txt", 'r')
Server_Messages = messageFile.readlines()
messageFile.close()

def changeName(args, clientArray): # changes Username
    print("args = ", args, len(args))
    if len(args) == 0:
        return[True, Server_Messages[4]]
    #change the user's username
    with open("users.txt", 'r') as file:
        lines = file.readlines()
        file.close()
    found = False
    currentUser = ()
    for l in lines:
        fullUser = l.partition(":")
        found = args[0] == fullUser[0]
        if fullUser[0] == clientArray[1]:
            currentUser = fullUser
        if found: break
    del lines, fullUser
    if found:
        del currentUser
        return [True, Server_Messages[12]]
    else:
        toSend = Server_Messages[16] + " " + args[0]
        currentUser_str = currentUser[0] + currentUser[1] + currentUser[2].replace("\n", '')
        newUser_str = args[0] + currentUser[1] + currentUser[2].replace("\n", '')
        print(currentUser_str)
        print(newUser_str)
        miscellaneous.findAndReplace("users.txt", newUser_str, currentUser_str)
        del currentUser, newUser_str, currentUser_str
        clientArray[1] = args[0]
        return [False, toSend]

def changePassword(args, clientArray): #changes Password
    print("args = ", args, len(args))
    if len(args) == 0:
        return[True, Server_Messages[13]]
    #change the user's password
    with open("users.txt", 'r') as file:
        lines = file.readlines()
        file.close()
    currentUser = ()
    for l in lines:
        fullUser = l.partition(":")
        if fullUser[0] == clientArray[1]:
            currentUser = fullUser
            break
    del lines, fullUser
    currentUser_str = currentUser[0] + currentUser[1] + currentUser[2].replace("\n", '')
    newUser_str = currentUser[0] + currentUser[1] + args[0]
    print(currentUser_str)
    print(newUser_str)
    miscellaneous.findAndReplace("users.txt", newUser_str, currentUser_str)
    del currentUser, newUser_str, currentUser_str
    return [False, Server_Messages[17]]

def createRoom(args, clientArray): #Needs to be Idiot-tested.
    perm_dict = {"public": True, "private": False, "protected": None,
                 True: "public", False: "private"}
    rName = ""
    perm = ""
    invites = [] #add invites later
    possibleRoom = None
    for room in clientArray[3]:
        if room.roomName[0:5] == "@temp":
            possibleRoom = room
            if possibleRoom.roomName[5] != "`": # then user has provided a good name before.
                rName = possibleRoom.roomName[5:]
            if not possibleRoom.isPublic is None:
                perm = perm_dict[possibleRoom.isPublic]
            break
    for a in args:
        if (a.lower() == "public" or a.lower() == "private") and not perm:
            perm = a
        elif a[0] == "[":
            newStr = a.replace("[", "")
            newStr = newStr.replace("]", "")
            newStr = newStr.replace(",", " ")
            invites = newStr.split(" ") # same as above. Adding invites later
        elif not rName:
            rName = "@temp" + a
    toSend = ""
    print(rName, perm, possibleRoom)
    if not rName:
        toSend += Server_Messages[21]
        rName = "@temp`" + clientArray[1]
    if not perm:
        toSend += Server_Messages[22]
        perm = "protected"
    if not possibleRoom:
        try:
            newRoom = Room.Room(rName, perm_dict[perm], clientArray[1], False)
        except FileExistsError:
            toSend += Server_Messages[23]
        else:
            clientArray[3].append(newRoom)
    else:
        possibleRoom.setName(rName, clientArray[1])
        possibleRoom.setPermission(perm_dict[perm], clientArray[1])
    if toSend:
        return [True, toSend]
    return [False, Server_Messages[24]]



str_to_function = {"name": changeName,
                   "password": changePassword,
                   "new_room": createRoom}
int_to_function = {7: changeName,
                   8: changePassword,
                   9: createRoom}
str_to_int = {"name": 7,
              "password": 8,
              "new_room": 9}