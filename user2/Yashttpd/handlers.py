import os
from mimetypes import guess_type
from importlib import import_module

### A very simple handler that responds to every request the exact same way.
def hello_world_handler(request_dict):
    html = '<html><body><h1>Hello World!</h1></body></html>'
    typ = 'text/html'
    return {'code':'200', 'message':html, 'headers':{'Content-Type':typ, 'Content-Length':str(len(html))}}

### A better handler, it reads the files the clients requests, and sends the right response.
def simple_static_handler(request_dict):
    if request_dict['method'] not in ['GET', 'HEAD']: return {'code':'501'} #not implemented
    resource = request_dict['uri'][1:]
    #the default webpage is our home page!
    if resource == '': resource = 'home.html'
    #make sure the resource exists. there ought to be more security checks here.
    #you don't want to tell people secrets!
    if not os.path.exists(resource): return {'code':'404'}
    typ, encoding = guess_type(resource)
    length = os.path.getsize(resource)
    headers = {'Content-Type':typ, 'Content-Length':str(length)}
    if encoding: headers['Content-Encoding'] = encoding
    response = {'code':'200', 'headers':headers}
    if request_dict['method'] == 'HEAD': return response
    message = open(resource)
    response['message'] = message.read()
    message.close()
    return response

### Next is a slightly better, more modular handler
def HEAD(request_dict):
    resource = request_dict['uri'][1:]
    if resource == '': resource = 'home.html'
    if not os.path.exists(resource): return {'code':'404'}
    typ, encoding = guess_type(resource)
    length = os.path.getsize(resource)
    headers = {'Content-Type':typ, 'Content-Length':str(length)}
    if encoding: headers['Content-Encoding'] = encoding
    #the resource key isn't looked at by the server
    return {'code':'200', 'headers':headers, 'resource':resource} 

def GET(request_dict):
    response = HEAD(request_dict)
    if len(response) == 1: return response
    resource = open(response['resource'])
    response['message'] = resource.read()
    resource.close()
    return response

def POST(request_dict):
    action = request_dict['uri'][1:]
    if not os.path.exists(action): return {'code':'404'}
    module = import_module(action[:-3])
    return module.main(request_dict)

def better_handler(request_dict):
    method = request_dict['method']
    if method == 'GET': return GET(request_dict)
    if method == 'HEAD': return HEAD(request_dict)
    if method == 'POST': return POST(request_dict)
    #Otherwise method is not implemented
    return {'code':'501'}

if __name__ == "__main__":
    from yashttpd import serve_forever
    from constants import IP, PORT, CHUNK, CONQ
    #serve_forever(IP, PORT, CONQ, CHUNK, simple_static_handler)
    serve_forever(IP, PORT, CONQ, CHUNK, better_handler)
