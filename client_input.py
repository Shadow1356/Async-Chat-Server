"""
This is where the user enters chat and commands
client_input creates files to be accessed by client_control.
"""
import os, sys

if sys.platform == "Windows":
    __dirPath = os.getcwd() + "\\messages\\"
else:
    __dirPath = os.getcwd() + "/messages/"

def Main():
    userInput = " "
    id = 1
    while userInput.lower() != "`exit":
        userInput = input(">>>>>> ")
        file = open((__dirPath + str(id) + ".ms"), 'w')
        file.write(userInput)
        file.close()
        id+= 1






if __name__ == "__main__":
    Main()