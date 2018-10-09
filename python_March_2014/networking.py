import socket, tools, custom, time, sys, select
from json import dumps as package, loads as unpackage
MAX_MESSAGE_SIZE = 60000
def serve_forever(handler, port, heart_queue='default', external=False):
    if heart_queue=='default':
        import Queue
        heart_queue=Queue.Queue()
    if external:
        host='0.0.0.0'
    else:
        host = 'localhost'
    backlog = 5
    time.sleep(1)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind((host,port))
    except:
        tools.kill_processes_using_ports([str(port)])
        tools.kill_processes_using_ports([str(port)])
        time.sleep(2)
        return serve_forever(handler, port, heart_queue)
    s.listen(backlog)
    while True:
        try:
            a=serve_once(s, MAX_MESSAGE_SIZE, handler)
            if a=='stop':
                s.close()
                tools.log('shutting off server: ' +str(port))
                return
        except Exception as exc:
            tools.log('networking error: ' +str(port))
            tools.log(exc)
def recvall(client, data=''):
    try:
        data+=client.recv(MAX_MESSAGE_SIZE)
    except:
        time.sleep(0.0001)
        tools.log('not ready')
        recvall(client, data)        
    if not data:
        return 'broken connection'
    if len(data)<5: return recvall(client, data)
    try:
        length=int(data[0:5])
    except:
        return 'no length'
    tries=0
    data=data[5:]
    while len(data)<length:
        d=client.recv(MAX_MESSAGE_SIZE-len(data))
        if not d:
            return 'broken connection'
        data+=d
    try:
        data=unpackage(data)
    except:
        pass
    return data
def serve_once(s, size, handler):
    client, address = s.accept()
    data=recvall(client)
    if data=='broken connection':
        #print('broken connection')
        return serve_once(s, size, handler)
    if data=='no length':
        #print('recieved data that did not start with its length')
        return serve_once(s, size, handler)
    if data=='stop': return 'stop'
    if data=='ping': data='pong'
    else: data=handler(data)
    send_msg(data, client)
    client.close() 
    return 0
def connect_error(msg, port, host, counter):
    if counter>3:
        return({'error':'could not get a response'})
    return(connect(msg, port, host, counter+1))
def send_msg(data, sock):
    data=tools.package(data)
    data=tools.buffer_(str(len(data)), 5)+data
    while data:
        time.sleep(0.0001)
        try:
            sent = sock.send(data)
        except:
            return 'peer died'
        data = data[sent:]
    return 0
def connect(msg, port, host='localhost', counter=0):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setblocking(5)
    try:
        s.connect((host,port))
    except:
        return({'error': 'cannot connect host:'+str(host) + ' port:' +str(port)})
    try:
        msg['version'] = custom.version
    except:
        pass
    r=send_msg(msg, s)
    if r=='peer died': return('peer died: ' +str(msg))
    data= recvall(s)
    if data=='broken connection':
        tools.log('broken connection: ' +str(msg))
        return(connect_error(msg, port, host, counter))
    if data=='no length':
        tools.log('no length: ' +str(msg))
        return(connect_error(msg, port, host, counter))
    return(data)
def send_command(peer, msg, response_time=1):
    return connect(msg, peer[1], peer[0])
if __name__ == "__main__":
    serve_forever(lambda x: x, 8000)
