"""
Miscellaneous module containing useful functions
not really belonging to one aspect of the program.
I don't really know what I'm doing.
"""

def replaceLine(path, line, string):
    readFile = open(path, 'r+')
    Lines = readFile.readlines()
    Lines[line-1] = string+'\n'
    readFile.seek(0)
    for elem in Lines:
        readFile.write(elem)
    readFile.close()

def findAndReplace(path, replace, old):
    readFile = open(path, 'r+')
    Lines = readFile.readlines()
    for i in range(len(Lines)):
        if old == Lines[i].replace('\n', ''):
            Lines[i] = replace+"\n"
    readFile.seek(0)
    for elem in Lines:
        readFile.write(elem)
    readFile.close()

def addToLine(path, line, string):
    readFile = open(path, 'r+')
    Lines = readFile.readlines()
    Lines[line-1] = Lines[line-1].replace("\n", "") + string+'\n'
    readFile.seek(0)
    for elem in Lines:
        readFile.write(elem)
    readFile.close()

if __name__ == "__main__":
    # replaceLine("Messages.txt", 1, "Test")
    # findAndReplace("Messages.txt", "Test", "Welcome")
    addToLine("Messages.txt", 2, " Test")