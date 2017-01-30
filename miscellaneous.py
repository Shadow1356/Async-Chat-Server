"""
Miscellaneous module containing useful functions
not really belonging to one aspect of the program.
I don't really know what I'm doing.
"""

def replaceLine(path, line, string): #replaces the line-th line with string in file:path (line : 1,2,3)
    readFile = open(path, 'r+')
    Lines = readFile.readlines()
    Lines[line-1] = string+'\n'
    readFile.seek(0)
    for elem in Lines:
        readFile.write(elem)
    readFile.close()

def findAndReplace(path, replace, old):#locates old and replaces it with replace
    readFile = open(path, 'r+')
    Lines = readFile.readlines()
    for i in range(len(Lines)):
        if old == Lines[i].replace('\n', ''):
            Lines[i] = replace+"\n"
    readFile.seek(0)
    for elem in Lines:
        readFile.write(elem)
    readFile.close()

def addToLine(path, line, string):#adds a new line (string) at line
    readFile = open(path, 'r+')
    Lines = readFile.readlines()
    Lines[line-1] = Lines[line-1].replace("\n", "") + string+'\n'
    readFile.seek(0)
    for elem in Lines:
        readFile.write(elem)
    readFile.close()

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

if __name__ == "__main__":
    # replaceLine("Messages.txt", 1, "Test")
    # findAndReplace("Messages.txt", "Test", "Welcome")
   # addToLine("Messages.txt", 2, " Test")
   cleanNewLines("users.txt")