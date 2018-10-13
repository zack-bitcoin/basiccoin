import urllib2, json
from time import sleep

node2url = {}
node2url[1] = "http://localhost:3011"
node2url[2] = "http://localhost:3021"
node2url[3] = "http://localhost:3031"
node2url_ext = {}
node2url_ext[1] = "http://localhost:3010"
node2url_ext[2] = "http://localhost:3020"
node2url_ext[3] = "http://localhost:3030"

def byteify(input):
    if isinstance(input, dict):
        return {byteify(key): byteify(value)
                for key, value in input.iteritems()}
    elif isinstance(input, list):
        return [byteify(element) for element in input]
    elif isinstance(input, unicode):
        return str(input)
    else:
        return input

def request(node, action, args, seconds_to_sleep=0):
    url = node2url[node]
    return request_helper(url, action, args, seconds_to_sleep)
def request_ext(node, action, args, seconds_to_sleep=0):
    url = node2url_ext[node]
    return request_helper(url, action, args, seconds_to_sleep)
def request_helper(url, action, args, seconds_to_sleep):
    d2 = json.dumps(byteify([action] + args))
    req = urllib2.Request(url=url, data = d2)
    #f = urlopen_with_retry(req)
    f = urllib2.urlopen(req)
    sleep(seconds_to_sleep)
    return f.read()
#def urlopen_with_retry(req, max_retry=5):
#    for _ in range(max_retry):
#        try:
#            return urllib2.urlopen(req)
#        except Exception:
#            sleep(5)
#    raise RuntimeError('Request failed {} times.'.format(max_retry))
