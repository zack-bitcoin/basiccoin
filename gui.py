#from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
#import string, cgi, time, networking, stackDB, copy, tools, pt
import networking, stackDB, copy, tools, pt, os, blockchain, custom, http
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
def main(port, brain_wallet, db):
    global DEFAULT_BRAIN
    global DB
    DEFAULT_BRAIN = brain_wallet
    DB = db
    ip = ''
    http.serve('localhost', port)
