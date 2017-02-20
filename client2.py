import threading, queue, socket, struct

class Receiver(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        with open("conn_info.txt") as file:
            self.IP, _, self.port, _ = file.readlines()
            file.close()
        self.done = False
        self.q = queue.Queue()
        self.raw_socket = socket.socket(socket.AF_INET,
                                        socket.SOCK_STREAM)
        self.raw_socket.setsockopt(socket.SOL_SOCKET,
                                   socket.SO_REUSEADDR, 1)
        self.raw_socket.bind(('', int(self.port)))
        self.raw_socket.listen(5)
        self.recv_sock, sockname = self.raw_socket.accept()
        self.recv_sock.shutdown(socket.SHUT_WR)
        self.recv_sock.settimeout(0.0)

    def run(self):
        while not self.done:
            try:
                message = self.recv_sock.recv(4096)
            except TimeoutError:
                print("TImeout Error Attempting to reconnect")
                self.recv_sock.close()
                self.raw_socket.close()
                del self.recv_sock, self.raw_socket
                self.__init__()
                continue
            except BlockingIOError:
                continue
            if message:
                self.q.put_nowait(message.decode("ascii"))
                message = ""
        self.recv_sock.close()
        self.raw_socket.close()


class Sender(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        with open("conn_info.txt") as file:
            self.IP, self.port, _, self.formatCharacter = file.readlines()
            file.close()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.IP, int(self.port)))
        self.sock.setblocking(False)
        self.sock.settimeout(0.0)
        print("Connected to ", self.IP, "with name: ", self.sock.getpeername())
        self.currentRoom = "@@broadcast@@"
        self.q = queue.Queue()
        self.done = False

    def run(self):
        while not self.done:
            if not self.q.empty():
                userInput = self.q.get(block = False)
                if userInput.lower() == '`exit':  # Close Stuff; need to finish
                    self.done = True #signal other threads.
                    break
                header = struct.Struct(self.formatCharacter)
                ##Need to add which room
                if userInput[0:2] == "`/":
                    separated = userInput[2:].partition(" ")
                    self.currentRoom = separated[0]
                    userInput = separated[2]
                toSend = userInput + ":`:" + self.currentRoom
                # ^ Rooms now handled by server.
                encoded_toSend = header.pack(len(toSend)) + toSend.encode("ascii")
                try:
                    self.sock.sendall(encoded_toSend)
                    print("Sent ", encoded_toSend, "to", self.sock)
                except socket.error as e:
                    print("Error was ", e)

        self.sock.close()

