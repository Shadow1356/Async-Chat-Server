"""
Miscellaneous module containing useful functions
not really belonging to one aspect of the program.
"""

def replaceLine(path, line, string): #replaces the line-th line with string in file:path (line : 1,2,3)
    readFile = open(path, 'r')
    Lines = readFile.readlines()
    Lines[line-1] = string+'\n'
    readFile.close()
    writeFile = open(path, 'w')
    for elem in Lines:
        writeFile.write(elem)
    writeFile.close()
    cleanNewLines(path)

def findAndReplace(path, replace, old):#locates old and replaces it with replace
    readFile = open(path, 'r+')
    Lines = readFile.readlines()
    for i in range(len(Lines)):
        if old in Lines[i].replace('\n', ''):
            print("REPLACING")
            newStr = Lines[i].replace(old, replace)
            Lines[i] = newStr
    readFile.close()
    writeFile = open(path, "w")
    for elem in Lines:
        writeFile.write(elem)
    writeFile.close()
    cleanNewLines(path)

def findAndReplaceLine(path, replace, old):
    readFile = open(path, 'r+')
    Lines = readFile.readlines()
    for i in range(len(Lines)):
        if old == Lines[i].replace('\n', ''):
            print("REPLACING")
            newStr = Lines[i].replace(old, replace)
            Lines[i] = newStr
    readFile.close()
    writeFile = open(path, "w")
    for elem in Lines:
        writeFile.write(elem)
    writeFile.close()
    cleanNewLines(path)

def addToLine(path, line, string):#adds a new line (string) at line
    readFile = open(path, 'r+')
    Lines = readFile.readlines()
    Lines[line-1] = Lines[line-1].replace("\n", "") + string+'\n'
    readFile.seek(0)
    for elem in Lines:
        readFile.write(elem)
    readFile.close()
    cleanNewLines(path)

def cleanNewLines(path): #gets rid of empty lines in path. (side effect of these functions)
    readFile = open(path, 'r')
    Lines = readFile.readlines()
    Cleaned = []
    for line in Lines:
        if line != "\n":
            Cleaned.append(line)
    readFile.close()
    writeFile = open(path, 'w')
    for elem in Cleaned:
        writeFile.write(elem)
    writeFile.close()

code_to_color = {"red":"red",
                 "blu": "blue",
                 "gre": "green",
                 "yel": "yellow",
                 "blk": "black",
                 "wht": "white",
                 "pup": "purple",
                 "pnk": "pink",
                 "org": "orange"}

colors = ("red", "blue", "green", "yellow", "black", "purple", "pink", "orange")


if __name__ == "__main__":
    # replaceLine("Messages.txt", 1, "Test")
    # findAndReplace("Messages.txt", "Test", "Welcome")
   # addToLine("Messages.txt", 2, " Test")
   replaceLine("users.txt", 4, "")