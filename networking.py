"""This file explains how sockets work for networking."""
import socket
import subprocess
import re
import tools
import custom
MAX_MESSAGE_SIZE = 60000


def kill_processes_using_ports(ports):
    popen = subprocess.Popen(['netstat', '-lpn'],
                             shell=False,
                             stdout=subprocess.PIPE)
    (data, err) = popen.communicate()
    pattern = "^tcp.*((?:{0})).* (?P<pid>[0-9]*)/.*$"
    pattern = pattern.format(')|(?:'.join(ports))
    prog = re.compile(pattern)
    for line in data.split('\n'):
        match = re.match(prog, line)
        if match:
            pid = match.group('pid')
            subprocess.Popen(['kill', '-9', pid])


def serve_forever(message_handler_func, PORT, queue):
    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('127.0.0.1', PORT))
    server.listen(100)
    while True:
        client, addr = server.accept()
        (ip, port) = addr
        data = client.recv(MAX_MESSAGE_SIZE)
        #we could insert security checks here
        data = tools.unpackage(data)
        client.sendall(tools.package(message_handler_func(data, queue)))


def connect(msg, host, port):
    msg['version'] = custom.version
    msg = tools.package(msg)
    if len(msg) < 1 or len(msg) > MAX_MESSAGE_SIZE:
        print('wrong sized message')
        return
    s = socket.socket()
    try:
        s.settimeout(2)
        s.connect((str(host), int(port)))
        s.sendall(msg)
        response = s.recv(MAX_MESSAGE_SIZE)
        #print(response)
        return tools.unpackage(response)
    except Exception as e:
        #print('THE ERROR WAS: ' +str(e))
        #print('disconnect')
        return {'error': e}


def send_command(peer, msg):
    return connect(msg, peer[0], peer[1])
