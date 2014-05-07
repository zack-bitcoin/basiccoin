from urlparse import parse_qs

def main(request_dict):
    stuff = parse_qs(request_dict['message'])
    junk = stuff['junk'][0]
    typ = 'text/plain'
    length = str(len(junk))
    return {'code':'200', 'message':junk, 'headers':{'Content-Type':typ, 'Content-Length':length}}
