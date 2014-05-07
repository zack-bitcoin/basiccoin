import networking, copy, tools, pt, os, blockchain, custom
DEFAULT_BRAIN=''#so that you don't have to type it in every time.
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
def page1(brainwallet=DEFAULT_BRAIN):
    out=empty_page
    out=out.format(easyForm('/home', 'Play Go!', '<input type="text" name="BrainWallet" value="{}">'.format(brainwallet)))
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
    out=out.format('<p>your address is: ' +str(tools.pub2addr(pubkey))+'</p>{}')
    out=out.format('<p>current block is: ' +str(DB['length'])+'</p>{}')
    try:
        balance=blockchain.db_get(pubkey, DB)
        balance=balance['amount']
    except:
        balance=0
    for tx in DB['txs']:
        if tx['type'] == 'spend' and tx['to'] == tools.pub2addr(pubkey):
            balance += tx['amount']
        if tx['type'] == 'spend' and tx['id'] == pubkey:
            balance -= tx['amount']
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
empty_page='<html><body>{}</body></html>'
def txt2src(txt):
    return "data:image/png;base64,"+txt






from Yashttpd import serve_forever, CHUNK, CONQ
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


def main(port, brain_wallet, db):
    global DEFAULT_BRAIN
    global DB
    DEFAULT_BRAIN = brain_wallet
    DB = db
    ip = ''
    serve('localhost', port)
