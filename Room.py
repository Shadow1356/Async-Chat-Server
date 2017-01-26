import os, platform, miscellaneous
from copy import deepcopy


class Room(object):
    def __init__(self, name, public, creator, loading):
        self.isPublic = public
        self.owner = creator
        self.Members = [creator]
        self.Admins = [creator]
        if platform.system() == "Windows":
            self.__roomDirPath = os.getcwd() + "\\RoomDir\\"
        else:
            self.__roomDirPath = os.getcwd() + "/RoomDir/"

        self.roomName = name
        self.__roomFile = self.__roomDirPath + name + ".txt"
        try:
            open(self.__roomFile, 'x').close()
        except FileExistsError as e:
            if loading:
                pass
            else:
                raise e  # then room name taken.
        else:
            self.__updateIndex(name)
        if not loading:
            newFile = open(self.__roomFile, 'w')
            newFile.write(str(self.isPublic) + '\n' + self.owner + '\n' + ":" + '\n' + ":" + "\n")
            newFile.close()

    def __str__(self):

        """Mostly for debugging purpose"""
        memberStr = ""
        for elem in self.Members:
            memberStr += elem + " "
        adminStr = ""
        for elem in self.Admins:
            adminStr += elem + " "
        return (self.roomName + " " + str(self.isPublic) + " " + self.owner + "\n\t" + memberStr +
                "\n\t" + adminStr)

    def __updateIndex(self, replace, old=None):
        readIndexFile = open((self.__roomDirPath + "__index__.txt"), 'r+')
        readIndexFile.seek(0, 2)

        if not old:  # old = None

            readIndexFile.write(replace + '\n')

        else:
            miscellaneous.findAndReplace((self.__roomDirPath + "__index__.txt"), replace, old)
            os.rename((self.__roomDirPath + old + ".txt"), (self.__roomDirPath + replace + ".txt"))
        readIndexFile.close()

    def setOwner(self, newOwner, requester):
        if requester != self.owner:
            raise PermissionError
        self.owner = newOwner
        if self.owner not in self.Members:
            self.Members.append(self.owner)
        if self.owner not in self.Admins:
            self.Admins.append(self.owner)
        # set file
        miscellaneous.replaceLine(self.__roomFile, 2, self.owner)

    def addAdmin(self, user, requester):
        if requester != self.owner:
            raise PermissionError
        if user in self.Admins:
            raise ValueError
        self.Admins.append(user)
        if user not in self.Members:
            self.Members.append(user)
        miscellaneous.addToLine(self.__roomFile, 4, (user + ":"))

    def deleteAdmin(self, admin, requester):
        if requester != self.owner:
            raise PermissionError
        if not admin in self.Admins:
            raise ValueError
        self.Admins.pop(self.Admins.index(admin))
        miscellaneous.findAndReplace(self.__roomFile, "", (admin+":"))
        print(admin, " deleted from ", self.roomName)

    def deleteRoom(self, requester):
        if requester != self.owner:
            raise PermissionError
        indexPath = self.__roomDirPath + "__index__.txt"
        miscellaneous.findAndReplaceLine(indexPath, "", self.roomName)
        os.remove(self.__roomFile)
        del self.roomName, self.Admins, self.Members, self.isPublic, self.owner, self.roomName

    def addMember(self, user, requester):
        if not self.isPublic and requester not in self.Admins:
            raise PermissionError
        self.Members.append(user)
        miscellaneous.addToLine(self.__roomFile, 3, (user + ":"))

    def deleteMember(self, user, requester):
        if not self.isPublic and requester not in self.Admins:
            raise PermissionError
        # print(self.roomName)
        # for elem in self.Members:
        #     print(elem, " = ", user, elem ==user)
        #     pass
        userIndex = self.Members.index(user)
        self.Members.pop(userIndex)
        miscellaneous.findAndReplace(self.__roomFile,"", (user+":"))
        print(user, " deleted from ", self.roomName)

    def setPermission(self, isPublic, requester):
        if requester != self.owner:
            raise PermissionError
        self.isPublic = isPublic
        miscellaneous.replaceLine(self.__roomFile, 1, str(isPublic))

    def setName(self, newName, requester):
        if requester != self.owner:
            raise PermissionError
        self.__updateIndex(newName, self.roomName)
        self.roomName = newName
        self.__roomFile = self.__roomDirPath + self.roomName + ".txt"


def LoadRooms():
    """Returns dict of Room Objects from the RoomDir Folder
        Room.roomName : Room Object
    """
    if platform.system() == "Windows":
        Path = os.getcwd() + "\\RoomDir\\"
    else:
        Path = os.getcwd() + "/RoomDir/"
    indexPath = Path + "__index__.txt"
    indexFile = open(indexPath, 'r')
    RoomsList = indexFile.readlines()
    Rooms = {}
    for elem in RoomsList:
        name = elem.replace("\n", "")
        roomFilePath = Path + name + ".txt"
        roomFile = open(roomFilePath, 'r')
        contents = roomFile.readlines()
        isPublic = (contents[0].replace('\n', '')) == 'True'
        owner = contents[1].replace('\n', '')

        # get admins from file using substrings

        admins = [owner]
        index = contents[3].rfind(':')
        lastIndex = len(contents[3])
        while index != -1:
            adm = (contents[3][index + 1:lastIndex]).replace('\n', '')
            if adm != "":
                admins.append(adm)
            lastIndex = index
            index = contents[3].rfind(':', 0, lastIndex)

        # get the members using substrings

        members = deepcopy(admins)

        index = contents[2].rfind(':')
        lastIndex = len(contents[2])
        while index != -1:
            mem = (contents[2][index + 1:lastIndex]).replace('\n', '')
            if mem != "":
                members.append(mem)
            lastIndex = index
            index = contents[2].rfind(':', 0, lastIndex)

        # End of File for now, make new ROom and append to Rooms


        newRoom = Room(name, isPublic, owner, True)

        newRoom.Members = deepcopy(members)
        newRoom.Admins = deepcopy(admins)
        Rooms[newRoom.roomName] = newRoom
    return Rooms


if __name__ == "__main__":
    try:
        newRoom = Room("@temptesting", False, "@@server", False)
    except FileExistsError:
        print("Name Taken.")
    newRoom.setName("testing", "@@server")

    # newRoom.setOwner("Nick", "ME")
    # newRoom.addAdmin("Scott", "Nick")
    # newRoom.addMember("Barry", "Nick")
    # newRoom.addMember("Wally", "Scott")
    # try:
    #     newRoom.addMember("Oliver", "Barry")
    # except PermissionError:
    #     print("User doesn't have permission.")
    # newRoom.setPermission(True, "Nick")
    # newRoom.addMember("Oliver", "Barry")
    # Rooms = LoadRooms()
    # for elem in Rooms:
    #     print(elem)

   # Broadcast = Room("@@broadcast@@", True, "@@server", False)