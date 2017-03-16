from tkinter import *
import client2
import queue
import threading
from ScrollingLabel2 import ScrollingLabel
from miscellaneous import code_to_color, colors
from random import randint

class ClientGUI(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.root = None
        self.output = None
        self.input = None
        self.enterButton = None
        self.menuBar = None
        self.fileMenu = None
        self.inQ = queue.Queue()
        self.outQ = queue.Queue()
        self.done = False

    def EnterAction(self, event=None):
        userInput = self.input.get()
        if not userInput:  # don't send an empty string
            return
        self.inQ.put(userInput)
        self.input.delete(0, END)

    def __update_output(self):
        #print("In update output")
        while not self.outQ.empty():
            outQ_list = self.outQ.get(block=False)
            self.output.add(outQ_list[0], outQ_list[1], outQ_list[2])

        self.root.after(500, self.__update_output)

    def run(self):
        self.root = Tk()
        self.root.geometry("750x650")
        self.root.resizable(False, False)
        self.root.wm_title("Chat Client")
        # Output History
        self.output = ScrollingLabel(self.root, 15,4, 50, 0, 0)
        print("THEre's a box")
        # Command Box
        self.input = Entry(self.root, width=50)
        self.input.place(x=375, y=600)
        # Enter Button
        self.enterButton = Button(self.root, text="ENTER", command=self.EnterAction)
        self.enterButton.place(x=700, y=600)
        ##Menu at top
        self.menuBar = Menu(self.root)
        self.fileMenu = Menu(self.menuBar)
        self.fileMenu.add_command(label="Open")
        self.fileMenu.add_separator()
        self.fileMenu.add_command(label="Exit", command=self.root.destroy)
        self.menuBar.add_cascade(label="File", menu=self.fileMenu)
        self.root.config(menu=self.menuBar)
        self.root.bind_all("<Button-1>", self.__printxy)
        self.root.bind_all("<Return>", self.EnterAction)
        self.root.protocol("WM_DELETE_WINDOW", self.__signalEnd)
        self.root.after(500, self.__update_output)
        self.root.mainloop()

    def __signalEnd(self):
        self.done = True
        self.root.destroy()

    def __printxy(self, event):
        print(event.x, " ", event.y)


class Client_Handler(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.sender = client2.Sender()
        self.receiver = client2.Receiver()
        self.client_gui = ClientGUI()
        self.Room_to_Color = {}
        self.User_to_Color = {}

    def run(self):
        while True:
            if self.sender.done: #doesn't work yet.
                self.receiver.done = True
                self.client_gui.done = True
                break
            if self.client_gui.done:
                self.receiver.done = True
                self.sender.done = True
                break
            if not self.receiver.q.empty():
                srv_message = self.receiver.q.get(block=False)
                print("Stuff in receiver's Q")
                self.interpret_message(srv_message)
            if not self.client_gui.inQ.empty():
                toSend = self.client_gui.inQ.get(block = False)
                self.sender.q.put_nowait(toSend)

    def connect(self):
        threads = [self.sender, self.receiver, self.client_gui, self]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

    def interpret_message(self, message):
        print("Parsing ", message)
        if message[0] == "Q":
            option_str, to_display = message[1:].split("::")
            option_list = option_str.split(":")
            self.client_gui.outQ.put_nowait((to_display, "", ""))
            popup_query = Popup(option_list, to_display)
            popup_query.start()
            popup_query.join()
            print("AFTER JOIN")
            while popup_query.return_value is None:
                pass
            self.sender.q.put_nowait(str(popup_query.return_value))
        elif message[0] == "M":
            self.client_gui.outQ.put_nowait((message[1:], "black", "white"))
        elif message[0] == "E":
            self.client_gui.outQ.put_nowait((message[1:], "red", "white"))
        elif message[0] == "C":
            room, user, _ = message[1:].split(":")
            bg = self.getColor(room, True)
            fg = self.getColor(user, False)
            self.client_gui.outQ.put_nowait((message[1:], fg, bg))
        elif message[0] == "W":
            # color = message[1:4]
            self.client_gui.outQ.put_nowait((message[1:], "", code_to_color["blu"]))
        else:
            raise ValueError

    def getColor(self, entity, isRoom):
        #might sub-class UserDict and overide __missing__ instead.
        if isRoom:
            if not entity in self.Room_to_Color:
                self.Room_to_Color[entity] = colors[randint(0, len(colors)-1)]
            return self.Room_to_Color[entity]
        if not entity in self.User_to_Color:
            self.User_to_Color[entity] = colors[randint(0, len(colors)-1)]
            return self.User_to_Color[entity]

class Popup(threading.Thread):
    def __init__(self, options, query):
        threading.Thread.__init__(self)
        self.top = None
        self.options = options
        self.query = query
        self.Buttons = []
        self.return_value = None

    def run(self):
        self.top = Toplevel()
        self.top.title(self.query)
        self.top.geometry("300x200")
        for opt in self.options:
            ID_index = self.options.index(opt)
            print("ID = ", ID_index)
            newButton = Button(self.top, text=opt,
                               command = lambda x = ID_index: self.clickOption(x))
            self.Buttons.append(newButton)
        for button in self.Buttons:
            button.pack()

    def clickOption(self, ID): # sets return value and closes window.
        self.return_value = ID
        self.top.destroy()

if __name__ == "__main__":
    Window = Client_Handler()
    Window.connect()
