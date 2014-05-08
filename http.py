from Yashttpd import serve_forever, CONQ, CHUNK
from urlparse import parse_qs
from mimetypes import guess_type
#gui.py uses this file to diplay html to browser.
def GET(DB, request_dict, func):
    path = request_dict['uri'][1:]
    message = func(DB)
    return {'code':'200', 'message':message, 
            'headers':{'Content-Type':'text/html', 'Content-Length':str(len(message))}}
def POST(DB, request_dict, func):
    path = request_dict['uri']
    if path != '/home': return {'code':'404'}
    field_info = parse_qs(request_dict['message'])
    fixes = ({key:val[0]} if len(val)>0 else {key:''} for key, val in field_info.items()) #generator
    for fix in fixes: field_info.update(fix)
    message = func(DB, field_info)
    return {'code':'200', 'message':message, 
            'headers':{'Content-Type':'text/html', 'Content-Length':str(len(message))}}
def server(DB, port, get_func, post_func):
    def handler(request_dict):
        method = request_dict['method']
        if method == 'GET': return GET(DB, request_dict, get_func)
        if method == 'POST': return POST(DB, request_dict, post_func)
        return {'code':'501'} #method not implemented
    serve_forever('localhost', port, CONQ, CHUNK, handler)
