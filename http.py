from yashttpd import serve_forever, CHUNK, CONQ
from urlparse import parse_qs
from mimetypes import guess_type


def GET(request_dict):
    path = request_dict['uri'][1:]
    if path == '':
        message = page1(DEFAULT_BRAIN)
        return {'code':'200', 'message':message, 'headers':{'Content-Type':'text/html', 'Content-Length':str(len(message))}}
    path = os.path.join(os.getcwd(), path)
    if not os.path.exists(path): return {'code':'404'} #not found
    typ_, encoding = guess_type(path)
    f = open(path)
    message = f.read()
    f.close()
    headers = {'Content-Type':typ_, 'Content-Length':str(len(message))}
    if encoding: headers.update({'Content-Encoding':encoding})
    return {'code':'200', 'message':message, 'headers':headers}

def POST(request_dict):
    path = request_dict['uri']
    if path != '/home': return {'code':'404'}
    field_info = parse_qs(request_dict['message'])
    fixes = ({key:val[0]} if len(val)>0 else {key:''} for key, val in field_info.items()) #generator
    for fix in fixes: field_info.update(fix)
    message = home(field_info, DB)
    return {'code':'200', 'message':message, 'headers':{'Content-Type':'text/html', 'Content-Length':str(len(message))}}

def handler(request_dict):
    method = request_dict['method']
    if method == 'GET': return GET(request_dict)
    if method == 'POST': return POST(request_dict)
    return {'code':'501'} #method not implemented

def serve(ip, port): return serve_forever(ip, port, CONQ, CHUNK, handler)
