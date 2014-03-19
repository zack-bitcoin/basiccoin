from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import urllib, json, blockchain, state_library, settings
#PORT=8070
#HTML
form='''
<form name="first" action="{}" method="{}">
<input type="submit" value="{}">{}
</form> {}
'''
newline='''<br />
{}'''
empty_page='<html><body>{}</body></html>'
#peers=['http://localhost:8071/tradeChain?dic={}',
#       'http://localhost:8072/tradeChain?dic={}',
#       'http://localhost:8073/tradeChain?dic={}',
#   ]
def test():
    dic='test'
    URL=[]
    for peer in peers:
        URL.append(urllib.urlopen(peer.format(package(dic))))
    return URL
def package(dic):
    return json.dumps(dic).encode('hex')
def unpackage(dic):
    return json.loads(dic.decode('hex'))
def easyForm(link, button_says, moreHtml='', typee='post'):
    a=form.format(link, '{}', button_says, moreHtml, "{}")
    if typee=='get':
        return a.format('get', '{}')
    else:
        return a.format('post', '{}')
linkHome = easyForm('/', 'HOME', '', 'get')
def page1(dic):
    out=empty_page
    out=out.format('<p>It Works!!</p>{}')
    return out.format('')
#server
def info(dic):
    state=state_library.current_state()
    chain=blockchain.load_chain()
    if 'version' not in dic or dic['version']!=settings.version:
        return package({'error':'wrong version'})
    else:
        dic.pop('version')
    if dic['type']=='blockCount':
        if len(chain)>0:
            return package({'length':state['length'], 'recent_hash':state['recent_hash']})
        else:
            return package({'length':0, 'recent_hash':0})
    if dic['type']=='rangeRequest':
        ran=dic['range']
        if ran[0]==0:
            ran[0]=1
        print('ran: ' +str(ran))
        if len(chain)>=int(ran[1]):
            print('$$$$$$$$$$dic: ' +str(dic))
            return package(chain[ran[0]:ran[1]+1])
        else:
            return package({'error':'oops'})
    if dic['type']=='transactions':
        return package(blockchain.load_transactions())
    if dic['type']=='backup_states':
        backups=state_library.fs_load(state_library.backup_db,[])
        for i in range(len(backups)):
            find_biggest=0
            if int(backups[i]['length'])<int(dic['start']) and int(backups[i]['length'])>int(find_biggest):
                find_biggest=int(i)
        return package(backups[find_biggest])
    if dic['type']=='pushtx':
        #blockchain.add_transaction(dic['tx'])
        #append this transaction to the list of suggested transactions.
        blockchain.push_appendDB('suggested_transactions.db', dic['tx'])
    if dic['type']=='pushblock':
        #blockchain.chain_push(dic['block'])
        #append this block to the list of suggested blocks.
        blockchain.push_appendDB('suggested_blocks.db', dic['block'])
def tradeChain(dic):
    print('dic: '+str(dic))
    if dic['type']=='tx':
         if blockchain.verify_transaction_pool(dic['transaction']):
            blockchain.add_transaction(dic['transaction'])
            return package({'response':'Recieved transaction'})
    print('ERROR--YOU WERE SENT A BAD TX!!')
    print(dic)
    return package({'error':'bad tx'})
class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        def url2dic(junk):#for in 'get'
            print('junk: ' +str(junk))
            junk=junk.split('&')
            dic={}
            for i in junk:
                a=i.split('=')
                if len(a)==2:
                    dic[a[0]]=a[1]
            return dic
        try:
            path=self.path
            if path == '/' or path[0:2] == '/?' :    
                if len(path)>1:
                    dic=url2dic(path[2:])
                else:
                    dic={}
                    self.send_response(200)
                    self.send_header('Content-type',    'text/html')
                    self.end_headers()
                    self.wfile.write(page1(dic))
                    return    
            locations=['/info?']
            for location in locations:
                if path[:len(location)]==location:
                    if len(path)>len(location)+1:
#                        dic=url2dic(path[len(location):])
                        print('location:' + str(location))
                        dic=unpackage(path[len(location):])
                    self.send_response(200)
                    self.send_header('Content-type',    'text/html')
                    self.end_headers()
                    if location=='/tradeChain?':
                        self.wfile.write(tradeChain(dic))
                    elif location=='/info?':                    
                        self.wfile.write(info(dic))
#                    elif location=='/pushtx?': 
#                        self.wfile.write(pushtx(dic))
#                    elif location=='/pushblock?': 
#                        self.wfile.write(pushblock(dic))
                    return
            filepath = self.path[1:] # remove leading '/'    
            if [].count(filepath)>0:
#               f = open( os.path.join(CWD, filepath), 'rb' )
                 #note that this potentially makes every file on your computer readable bny the internet
                self.send_response(200)
                self.send_header('Content-type',    'application/octet-stream')
                self.end_headers()
                #                    self.wfile.write(f.read())
                #                    f.close()
            else:
                self.send_response(200)
                self.send_header('Content-type',    'text/html')
                self.end_headers()
                self.wfile.write("<h5>Don't do that</h5>")
            return
        except IOError as e :  
            print e
            self.send_error(404,'File Not Found: %s' % self.path)
    def do_POST(self):
        print("path: " + str(self.path))
        #         try:
        ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))    
        print(ctype)
        if ctype == 'multipart/form-data' or ctype=='application/x-www-form-urlencoded':    
            fs = cgi.FieldStorage( fp = self.rfile,
                                   headers = self.headers, # headers_,
                                   environ={ 'REQUEST_METHOD':'POST' })
        else: raise Exception("Unexpected POST request")
        self.send_response(200)
        self.end_headers()
        def fs2dic(fs):#for in "post"
            dic={}
            for i in fs.keys():
                a=fs.getlist(i)
                if len(a)>0:
                    dic[i]=fs.getlist(i)[0]
                else:
                    dic[i]=""
            return dic
        dic=fs2dic(fs)
        if self.path=='/':
            self.wfile.write(page1(dic))
        else:
            print('ERROR: path {} is not programmed'.format(str(self.path)))
def main(port):
    try:
        server = HTTPServer(('', port), MyHandler)
        print 'started httpserver...'
        server.serve_forever()
    except KeyboardInterrupt:
        print '^C received, shutting down server'
        server.socket.close()
#if __name__ == '__main__':
#    main()

