from tkinter import *
import client2
import queue
import threading

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
            self.output.insert(END, self.outQ.get(block=False))
        self.root.after(500, self.__update_output)

    def run(self):
        self.root = Tk()
        self.root.geometry("750x650")
        self.root.resizable(False, False)
        self.root.wm_title("Chat Client")
        # Output History
        self.output = Listbox(self.root, height=40, width=60)
        print("THEre's a box")
        self.output.place(x=0, y=0)
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
        self.root.after(1, self.__update_output)
        self.root.mainloop()



    def __printxy(self, event):
        print(event.x, " ", event.y)

class Client(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.sender = client2.Sender()
        self.receiver = client2.Receiver()
        self.client_gui = ClientGUI()
        self.q = queue.Queue()

    def run(self):
        while True:
            if self.sender.done:
                self.receiver.done = True
                self.client_gui.done = True
                break
            if not self.receiver.q.empty():
                srv_message = self.receiver.q.get(block=False)
                print("Stuff in receiver's Q")
                self.client_gui.outQ.put(srv_message)
            if not self.client_gui.inQ.empty():
                toSend = self.client_gui.inQ.get(block = False)
                self.sender.q.put_nowait(toSend)


    def connect(self):
        self.sender.start()
        self.receiver.start()
        self.client_gui.start()
        self.start()
        self.sender.join()
        self.receiver.join()
        self.client_gui.join()
        self.join()



if __name__ == "__main__":
    Window = Client()

    Window.connect()
