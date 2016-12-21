"""
Module for the commands the user can invoke in the chat.
"""
import miscellaneous
messageFile = open("Messages.txt", 'r')
Server_Messages = messageFile.readlines()
messageFile.close()

def changeName(args, clientArray):
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

def changePassword(args, clientArray):
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

str_to_function = {"name": changeName,
                   "password": changePassword}
int_to_function = {7: changeName,
                   8: changePassword}
str_to_int = {"name": 7,
              "password": 8}