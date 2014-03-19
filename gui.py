from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import string,cgi,time, json, random, copy, pickle, os, settings
import blockchain, state_library, message
import message as msg_lib
import pybitcointools as pt
spend_list=msg_lib.spend_list
def spend(amount, pubkey, privkey, to_pubkey, state):
    amount=int(amount*(10**5))
    tx={'type':'spend', 'id':pubkey, 'amount':amount, 'to':to_pubkey}
    easy_add_transaction(tx, spend_list, privkey, state)
def messager(board, pubkey, privkey, state, message):
    tx={'type':'message', 'board':board, 'id':pubkey, 'message':message}
    easy_add_transaction(tx, msg_lib.message_list, privkey, state)
def easy_add_transaction(tx_orig, sign_over, privkey, state):
    print('tx: ' +str(tx_orig))
    tx=copy.deepcopy(tx_orig)
    pubkey=pt.privtopub(privkey)
    if pubkey not in state or 'count' not in state[pubkey]:
        tx['count']=1
    else:
        tx['count']=state[pubkey]['count']
    txs=blockchain.load_transactions()
    my_txs=filter(lambda x: x['id']==pubkey, txs)
    tx['signature']=pt.ecdsa_sign(msg_lib.message2signObject(tx, sign_over), privkey)
    if blockchain.add_transaction(tx):
        blockchain.pushtx(tx, settings.peers_list)
        return True
    if 'move_number' in tx:
        for i in range(10):
            tx['move_number']+=1
            tx['signature']=pt.ecdsa_sign(msg_lib.message2signObject(tx, sign_over), privkey)
            if blockchain.add_transaction(tx):
                blockchain.pushtx(tx, settings.peers_list)
                return True
    print('SOMETHING IS BROKEN')
    return False
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
active_games=[]
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
def home(dic):
    if 'BrainWallet' in dic:
        dic['privkey']=pt.sha256(dic['BrainWallet'])
    elif 'privkey' not in dic:
        return "<p>You didn't type in your brain wallet.</p>"
    privkey=dic['privkey']
    pubkey=pt.privtopub(dic['privkey'])
    def clean_state():
        transactions=blockchain.load_transactions()
        state=state_library.current_state()
        a=blockchain.verify_transactions(transactions, state)
        print('a: ' +str(a))
        return a['newstate']
    state=clean_state()
    if 'do' in dic.keys():
        if dic['do']=='spend':
            try:
                spend(float(dic['amount']), pubkey, privkey, dic['to'], state)
            except:
                pass
        state=clean_state()
    out=empty_page
    out=out.format('<p>your address is: ' +str(pubkey)+'</p>{}')
    print('state: ' +str(state))
    out=out.format('<p>current block is: ' +str(state['length'])+'</p>{}')
    if pubkey not in state:
        state[pubkey]={'amount':0}
    if 'amount' not in state[pubkey]:
        state[pubkey]['amount']=0
    out=out.format('<p>current balance is: ' +str(state[pubkey]['amount']/100000.0)+'</p>{}')        
    if state[pubkey]['amount']>0:
        out=out.format(easyForm('/home', 'spend money', '''
        <input type="hidden" name="do" value="spend">
        <input type="text" name="to" value="address to give to">
        <input type="text" name="amount" value="amount to spend">
        <input type="hidden" name="privkey" value="{}">'''.format(privkey)))    
    s=easyForm('/home', 'Refresh', '''    <input type="hidden" name="privkey" value="{}">'''.format(privkey))
    out=out.format(s)
    out=out.format(easyForm('/board', 'Read Board', '''
    <input type="hidden" name="privkey" value="{}">
    <input type="text" name="board" value="board name">
    '''.format(privkey)))
    return out
    
def board(dic):
    privkey=dic['privkey']
    board=dic['board']
    pubkey=pt.privtopub(dic['privkey'])
    def clean_state():
        transactions=blockchain.load_transactions()
        state=state_library.current_state()
        return blockchain.verify_transactions(transactions, state)['newstate']
    state=clean_state()
    if 'do' in dic.keys():
        if dic['do']=='message':
            print('board: ' +str(board))
            print('type: ' +str(type(board)))
            messager(board, pubkey, privkey, state, dic['message'])
        state=clean_state()#so you can see your message immediately after you type it. otherwise you have to wait for the page to refresh.
    out=empty_page
    out=out.format('<p>your address is: ' +str(pubkey)+'</p>{}')
    out=out.format('<p>current block is: ' +str(state['length'])+'</p>{}')
    if pubkey not in state:
        state[pubkey]={'amount':0}
    if 'amount' not in state[pubkey]:
        state[pubkey]['amount']=0
    out=out.format('<p>current balance is: ' +str(state[pubkey]['amount']/100000.0)+'</p>{}')
    if 'board' not in dic:
        return out.format('<p>oops. I can not remember what board we were looking at.</p>')
    s=easyForm('/board', 'refresh', '''    <input type="hidden" name="privkey" value="{}"><input type="hidden" name="board" value="{}">'''.format(privkey, board))
    out=out.format(s)
    s=easyForm('/home', 'main menu', '''    <input type="hidden" name="privkey" value="{}"><input type="hidden" name="board" value="{}">'''.format(privkey, board))
    out=out.format(s)
    out=out.format("<h1>"+str(board)+"</h1>{}")
    for i in state[board]:
        out=out.format("<p>"+i+"</p>{}")
    out=out.format(easyForm('/board', 'leave a comment', '''
    <input type="hidden" name="do" value="message">
    <input type="text" name="message" value="">
    <input type="hidden" name="privkey" value="{}">
    <input type="hidden" name="board"  value="{}">'''.format(privkey, board)))
    return out.format('')
def hex2htmlPicture(string, size):
    return '<img height="{}" src="data:image/png;base64,{}">{}'.format(str(size), string, '{}')
#def file2hexPicture(fil):
#    return image64.convert(fil)
#def file2htmlPicture(fil):
#    return hex2htmlPicture(file2hexPicture(fil))
def newline():
    return '''<br />
{}'''
empty_page='''<html><head></head><body>{}</body></html>'''
initial_db={}
database='tags.db'
def txt2src(txt):
    return "data:image/png;base64,"+txt
class MyHandler(BaseHTTPRequestHandler):
   def do_GET(self):
      try:
         if self.path == '/' :    
#            page = make_index( '.' )
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
            jan_script='''
<head><script>
function refreshPage () {
//save y position
localStorage.scrollTop = window.scrollY
// no reload instead posting a hidden form
document.getElementsByName("first")[0].submit()
}

window.onload = function () {

//setting position if available
if(localStorage.scrollTop != undefined) {
window.scrollTo(0, localStorage.scrollTop);    
}
//refresh loop
setTimeout(refreshPage, 3000);
}
</script></head>
'''
            if self.path=='/home':
                self.wfile.write(home(dic))
            if self.path=='/board':
#                   self.wfile.write(board(dic).replace('<head></head>', jan_script))
                   self.wfile.write(board(dic))#.replace('<head></head>', jan_script))
            else:
                print('ERROR: path {} is not programmed'.format(str(self.path)))
default_brain=''
def main(PORT, brain_wallet):
    global default_brain
    default_brain=brain_wallet
    try:
        server = HTTPServer(('', PORT), MyHandler)
        print 'started httpserver...'
        server.serve_forever()
    except KeyboardInterrupt:
        print '^C received, shutting down server'
        server.socket.close()
if __name__ == '__main__':
    main(settings.gui_port, settings.brain_wallet)
