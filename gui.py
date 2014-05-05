from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import string, cgi, time, networking, stackDB, copy, tools, pt
import blockchain, custom
def spend(amount, pubkey, privkey, to_pubkey, DB):
    amount=int(amount*(10**5))
    tx={'type':'spend', 'id':pubkey, 'amount':amount, 'to':to_pubkey}
    easy_add_transaction(tx, privkey, DB)
def easy_add_transaction(tx_orig, privkey, DB):
    tx=copy.deepcopy(tx_orig)
    pubkey=pt.privtopub(privkey)
    try:
        tx['count']=blockchain.count(pubkey, DB)
    except:
        tx['count']=1
    tx['signature']=pt.ecdsa_sign(tools.det_hash(tx), privkey)
    blockchain.add_tx(tx, DB)
def fs2dic(fs):
    dic={}
    for i in fs.keys():
        a=fs.getlist(i)
        if len(a)>0:
            dic[i]=fs.getlist(i)[0]
        else:
            dic[i]=""
    return dic
submit_form='''
<form name="first" action="{}" method="{}">
<input type="submit" value="{}">{}
</form> {}
'''
def easyForm(link, button_says, moreHtml='', typee='post'):
    a=submit_form.format(link, '{}', button_says, moreHtml, "{}")
    if typee=='get':
        return a.format('get', '{}')
    else:
        return a.format('post', '{}')
linkHome = easyForm('/', 'HOME', '', 'get')

def page1(default_brainwallet=''):
    out=empty_page
    out=out.format(easyForm('/home', 'Play Go!', '<input type="text" name="BrainWallet" value="{}">'.format(default_brainwallet)))
    return out.format('')
def home(dic, DB):
    if 'BrainWallet' in dic:
        dic['privkey']=pt.sha256(dic['BrainWallet'])
    elif 'privkey' not in dic:
        return "<p>You didn't type in your brain wallet.</p>"
    privkey=dic['privkey']
    pubkey=pt.privtopub(dic['privkey'])
    if 'do' in dic.keys():
        if dic['do']=='spend':
            spend(float(dic['amount']), pubkey, privkey, dic['to'], DB)
    out=empty_page
    out=out.format('<p>your address is: ' +str(pubkey)+'</p>{}')
    out=out.format('<p>current block is: ' +str(DB['length'])+'</p>{}')
    try:
        balance=blockchain.db_get(pubkey, DB)
        print('$$$$$$$$$$$$$$$$$$$$balance: ' +str(balance))
        balance=balance['amount']
    except:
        balance=0
    out=out.format('<p>current balance is: ' +str(balance/100000.0)+'</p>{}')
    if balance>0:
        out=out.format(easyForm('/home', 'spend money', '''
        <input type="hidden" name="do" value="spend">
        <input type="text" name="to" value="address to give to">
        <input type="text" name="amount" value="amount to spend">
        <input type="hidden" name="privkey" value="{}">'''.format(privkey)))    
    s=easyForm('/home', 'Refresh', '''    <input type="hidden" name="privkey" value="{}">'''.format(privkey))
    return out.format(s)
def hex2htmlPicture(string, size):
    return '<img height="{}" src="data:image/png;base64,{}">{}'.format(str(size), string, '{}')
def newline():
    return '''<br />
{}'''
empty_page='''<html><head></head><body>{}</body></html>'''
def txt2src(txt):
    return "data:image/png;base64,"+txt
class MyHandler(BaseHTTPRequestHandler):
   def do_GET(self):
      try:
         if self.path == '/' :    
            self.send_response(200)
            self.send_header('Content-type',    'text/html')
            self.end_headers()
            self.wfile.write(page1(default_brain))
            return    
         else : # default: just send the file    
            filepath = self.path[1:] # remove leading '/'    
            if [].count(filepath)>0:
#               f = open( os.path.join(CWD, filepath), 'rb' )
                 #note that this potentially makes every file on your computer readable bny the internet
               self.send_response(200)
               self.send_header('Content-type',    'application/octet-stream')
               self.end_headers()
               self.wfile.write(f.read())
               f.close()
            else:
               self.send_response(200)
               self.send_header('Content-type',    'text/html')
               self.end_headers()
               self.wfile.write("<h5>Don't do that</h5>")
            return
         return # be sure not to fall into "except:" clause ?      
      except IOError as e :  
             # debug    
         print e
         self.send_error(404,'File Not Found: %s' % self.path)
   def do_POST(self):
            print("path: " + str(self.path))
            ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))    
            print(ctype)
            if ctype == 'multipart/form-data' or ctype=='application/x-www-form-urlencoded':    
               fs = cgi.FieldStorage( fp = self.rfile,
                                      headers = self.headers, # headers_,
                                      environ={ 'REQUEST_METHOD':'POST' })
            else: raise Exception("Unexpected POST request")
            self.send_response(200)
            self.end_headers()
            dic=fs2dic(fs)
            if self.path=='/home':
                self.wfile.write(home(dic, DB))
            else:
                print('ERROR: path {} is not programmed'.format(str(self.path)))
default_brain=''#so that you don't have to type it in every time.
def main(PORT, brain_wallet, db):
    global default_brain
    global DB
    DB=db
    default_brain=brain_wallet
    try:
        server = HTTPServer(('', PORT), MyHandler)
        print 'started httpserver...'
        server.serve_forever()
    except KeyboardInterrupt:
        print '^C received, shutting down server'
        server.socket.close()
#if __name__ == '__main__':
#    networking.kill_processes_using_ports([str(custom.gui_port)])
#    main(custom.gui_port, custom.privkey, leveldb.levelDB)
