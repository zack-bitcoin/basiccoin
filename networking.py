"""This file explains how sockets work for networking."""
import socket
import tools
import custom
import time
import sys
MAX_MESSAGE_SIZE = 60000
def recvall(sock, max_size, Timespan=1):
    data = ''
    tries=0
    while not tools.can_unpack(data):
        sleep_chunk=0.01
        time.sleep(sleep_chunk)
        tries+=1
        if tries>Timespan/sleep_chunk:
            return {'recvall timeout error': data}
        try:
            d=sock.recv(max_size - len(data))
            if not d:
                return {'recvall connection broken error':data}
            data += d
        except:
            pass
    return data
def sendall(sock, data):
    while data:
        time.sleep(0.1)
        sent = sock.send(data)
        data = data[sent:]
def connect_socket(sock, ip, port):
    tries=0
    while True:
        time.sleep(0.2)
        tries+=1
        if tries>20: return False
        try:
            sock.connect((ip, port))
            return True
        except:
            pass
def serve_forever(PORT, handler, heart_queue, DB):
    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    time.sleep(2)
    heart_queue.put('server: '+str(PORT))
    #print('before bind')
    try:
        server.bind(('0.0.0.0', PORT))
    except:
        tools.kill_processes_using_ports([str(PORT)])
        return serve_forever(PORT, handler, heart_queue, DB)
    #print('after bind')
    server.listen(100)
    server.setblocking(0)
    try:
        while True:
            if DB['stop']: return
            serve_once(PORT, handler, heart_queue, server)
    except:
        print('serve forever error: ' +str(sys.exc_info()))
def serve_once(PORT, handler, heart_queue, server):
    heart_queue.put('server: '+str(PORT))
    time.sleep(0.1)
    #try:
    try:
        client, addr = server.accept()
    except:
        return
    (ip, port) = addr
    peer=[str(ip), int(port)]
    try:
        data=recvall(client, MAX_MESSAGE_SIZE)
    except:
        client.close()
        return
    if type(data)==type('string'):
        data=tools.unpackage(data)
    data['peer']=peer
    try:
        sendall(client, tools.package(handler(data)))
    except:
        pass
    client.close()
    #except:
    #    pass
def connect(msg, host, port, response_time=1):
    if len(msg) < 1 or len(msg) > MAX_MESSAGE_SIZE:
        tools.log('wrong sized message')
        return('wrong size')
    s = socket.socket()
    s.setblocking(0)
    b=connect_socket(s, str(host), int(port))
    if not b: 
        s.close()
        return ({'error':'cannot connect: '+str(host)})
    msg['version'] = custom.version
    sendall(s, tools.package(msg))
    response=recvall(s, MAX_MESSAGE_SIZE, response_time)
    s.close()
    try:
        return tools.unpackage(response)
    except:
        pass
    if 'recvall timeout error' in response:
        return({'error':'cannot download: '+str(host)})
def send_command(peer, msg, response_time=1):
    return connect(msg, peer[0], peer[1], response_time)
