from tkinter import *

class ScrollingLabel:
    def __init__(self, window, num_of_labels, height, width, x, y):
        self._size = num_of_labels
        self._height = height
        self._width = width
        self._root = window
        self._xpos = x
        self._ypos = y
        self._labels = []
        self._master = [""] * self._size
        self._current_bottom = 0
        self._relative_bottom =-1
        self.FGColor = "white"
        self.BGColor = "black"
        self._upButton = Button(self._root, text="/\\",
                                command=self._up)
        self._downButton = Button(self._root, text="\\/",
                                  command=self._down)
        self._upButton.place(x=self._xpos+self._width*7.5, y=self._ypos)
        self._downButton.place(x=self._xpos+self._width*7.5, y=self._ypos+25)
        for i in range(self._size):
            txtVar = StringVar()
            newLabel = Label(self._root, bg=self.BGColor,
                             fg=self.FGColor, height=self._height,
                             width=self._width, textvariable=txtVar)
            self._labels.append((newLabel, txtVar))
        current_y = self._ypos
        print(self._labels)
        for label, _ in self._labels:
            label.place(x=self._xpos, y=current_y)
            current_y += (height*10)
        # self._labels[0][1].set("This is zero")

    def _up(self):
       # print(self._relative_bottom)
        if self._relative_bottom == -1:
            self._relative_bottom = self._current_bottom
        if self._relative_bottom !=self._size-1:
            self._relative_bottom -=1
            self._update(self._relative_bottom)

    def _down(self):
        if self._relative_bottom == -1:
            self._relative_bottom = self._current_bottom
        if self._relative_bottom !=len(self._master)-1:
            self._relative_bottom +=1
            self._update(self._relative_bottom)

    def _update(self, r_bottom):
        master_index = r_bottom
        for index in reversed(range(self._size)):
           # print("Master Index value = ", self._master[master_index])
            if not self._master[master_index]:
                master_index-=1
                if master_index <0:
                    master_index = len(self._master) -1
                continue
            self._labels[index][1].set(self._master[master_index][0])
            if self._master[master_index][1]:
                self._labels[index][0].configure(fg=self._master[master_index][1])
            if self._master[master_index][2]:
                self._labels[index][0].configure(bg=self._master[master_index][2])
            master_index -= 1
            if master_index < 0:
                master_index = len(self._master) - 1

    def add(self, text, fg="", bg=""): #implement colors later
        for i in range(self._size):
            if not self._master[i]:
                self._master[i] = (text, fg, bg)
                self._current_bottom = i
                break
        else:
            self._master.append((text, fg, bg))
            self._current_bottom += 1

       # print("Master = ", self._master)
        self._relative_bottom = -1
        self._update(self._current_bottom)



if __name__ == "__main__":
    root = Tk()
    root.geometry("750x650")
    chatWindow = ScrollingLabel(root, 3, 4, 15, 0, 0)
    chatWindow.add("Hello")
    chatWindow.add("This is a test")
    chatWindow.add("Almost Gone")
    chatWindow.add("HEllo is gone!")
    chatWindow.add("MDSLD")
    # chatWindow.add("Hello", False)
    # chatWindow.add("This is a test", False)
    # chatWindow.add("Almost Gone", False)
    # chatWindow.add("HEllo is gone!", False)
    # chatWindow.add("MDSLD", False)
    # chatWindow.add("bottom")
    # chatWindow.add("Top", False)
    root.mainloop()
