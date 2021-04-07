# Reverse Shell
This is a reverse shell script written in python.

## Usage
### Server 
```python3 server.py```
#### arguments:
- ```-p "port"``` or ```--port "port"```
    - By default the server binds to port 41369.
    - To change to any other number use -p ... or --port ...
    - For example: if you want to run the server at port 22222
    - ```python3 server.py -p 22222``` or ```python3 server.py --port 22222```

#### commands:
- To list all current connections type list

- To connect to a machine type their numeric id

- To receive files type ```receive "file"``` while in the client's console to receive a file(must be on the same dir)
    The files will be copied into a folder called received_files at the directory server.py runs at.

- To send files type ```send "file"```. File to be sent must be in a directory called send that's in the same
directory as server.py. It must be run at the client's console and the file will be copied into the directory
the client shell is in.
    
### Client
```python3 client.py "ip" "port"```
#### arguments:
- ip: the ip of the server(this is required)
- port: the port the server is bound to (this is also required)
- ```-v```, ```--verbose```: a verbose output of what the server is running in the local shell
- ```-l```, ```--loop```: the client program will never halt unless an outside kill signal is sent.
it will attempt to connect indefinitely

This comes with neither warranty nor working guarantee whatsoever. If you do, use at your own risk.
I do not accept any responsibility of any sorts. Don't use this on systems that you
have no written consent to do so.
