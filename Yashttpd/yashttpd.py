import socket
from string import strip
from json import dumps as package
from constants import HTTP_VERS, HTTP_CODES
from sys import stdout

VERBOSE=False
def print_(txt):
    if VERBOSE: print(txt)

def make_server(ip, port, conq):
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((ip, port))
    s.listen(conq)
    print_("socket #%d listening @ %s:%d" % (s.fileno(), ip, port))
    return s

def pretty(dic):
    print_(package(dic, sort_keys=True, indent=4))

def parse_request(client, address, chunk):
    message = client.recv(chunk)
    request, message = message.split("\r\n", 1)
    request = request.split(' ', 3)
    headers, message = message.split("\r\n\r\n", 1)
    headers = headers.split("\r\n")
    request_dict = dict(zip(('method', 'uri', 'version'), request))
    headers = [map(strip, line.split(':', 1)) for line in headers] 
    request_dict['headers'] = dict(headers)
    request_dict['message'] = message
    print_('parsing request from'+str(address))
    pretty(request_dict)
    return request_dict

def send_response(client, address, response_dict):
    print_('responding to'+str(address))
    pretty(response_dict)
    code = response_dict['code']
    code_msg = HTTP_CODES[int(code)][0]
    response = HTTP_VERS + ' ' +  code + ' ' + code_msg + '\r\n'
    client.send(response)
    headers = '\r\n'.join(': '.join(item) for item in response_dict.get('headers', {}).items())
    client.send(headers + '\r\n\r\n')
    client.send(response_dict.get('message', ''))

def serve_forever(ip, port, conq, chunk, handler):
        s = make_server(ip, port, conq)
        try:
            while True:
                c, a = s.accept()
                request_dict = parse_request(c, a, chunk)
                response_dict = handler(request_dict)
                send_response(c, a, response_dict)
                c.close()
        except KeyboardInterrupt:
            stdout.write("\r")
            stdout.flush()
            print_('shutting down')
            for sock in [c, s]:
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                    sock.close()
                except:
                    pass

if __name__ == "__main__":
    from constants import IP, PORT, CONQ, CHUNK
    
    def handler(request_dict):
        #Normally, you would actually look at the contents of
        #request_dict and determine create your response_dict
        #from that. This is just a demo.
        html = '<html><body><h1>Hello World!</h1></body></html>'
        typ = 'text/html'
        return {'code':'200', 'message':html, 'headers':{'Content-Type':typ, 'Content-Length':str(len(html))}}

    serve_forever(IP, PORT, CONQ, CHUNK, handler)
