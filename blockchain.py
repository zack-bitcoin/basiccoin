import string,cgi,time, json, random, copy, os, copy, urllib, message, urllib2, time, settings
import pybitcointools as pt
import state_library
genesis={'zack':'zack', 'length':-1, 'nonce':'22', 'sha':'00000000000'}
genesisbitcoin=291266-1224#1220
chain=[genesis]
chain_db='chain.db'
transactions_database='transactions.db'

#I call my database appendDB because this type of database is very fast to append data to.
def line2dic(line):
    return json.loads(line.strip('\n'))
def load_appendDB(file):
    out=[]
    try:
        with open(file, 'rb') as myfile:
            a=myfile.readlines()
            for i in a:
                if i.__contains__('"'):
                    out.append(line2dic(i))
    except:
        pass
    return out
def ex(db_extention, db):
    return db.replace('.db', db_extention+'.db')
def load_transactions(db_extention=""):
    return load_appendDB(ex(db_extention, transactions_database))
def load_chain(db_extention=''):
    open(ex(db_extention, chain_db), 'a').close()
    current=load_appendDB(ex(db_extention, chain_db))
    if len(current)<1:
        return [genesis]
    if current[0]!=genesis:
        current=[genesis]+current
    return current
def reset_appendDB(file):
    open(file, 'w').close()
def reset_transactions(db_ex=''):
    return reset_appendDB(ex(db_ex, transactions_database))
def reset_chain(db_ex=''):
    return reset_appendDB(ex(db_ex, chain_db))
def push_appendDB(file, tx):
    with open(file, 'a') as myfile:
        myfile.write(json.dumps(tx)+'\n')
def add_transactions(txs, db_ex=''):#to local pool
    #This function is order txs**2, that is risky
    txs_orig=copy.deepcopy(txs)
    count=0
#    print('txs: ' +str(txs_orig))
    if 'error' in txs:
        return
    for tx in sorted(txs_orig, key=lambda x: x['count']):
        if add_transaction(tx, db_ex):
            count+=1
            txs.remove(tx)
    if count>0:
        add_transactions(txs, db_ex)
def add_transaction(tx, db_ex=''):#to local pool
    if tx['type']=='mint':
        return False
    transactions=load_transactions(db_ex)
    state=state_library.current_state(db_ex)
    if verify_transactions(transactions+[tx], state)['bool']:
        push_appendDB(ex(db_ex, transactions_database), tx)
        return True
    return False
def chain_push(block, db_extention=''):
    statee=state_library.current_state(db_extention)    
    print('CHAIN PUSH')
    if new_block_check(block, statee):
        print('PASSED TESTS')
        state=verify_transactions(block['transactions'], statee)
        state=state['newstate']
        state['length']+=1
        state['recent_hash']=block['sha']
        state_library.save_state(state, db_extention)
        if block['length']%10==0 and block['length']>11:
            state_library.backup_state(state, db_extention)
        txs=load_transactions(db_extention)
        reset_transactions(db_extention)
        add_transactions(txs, db_extention)
        return push_appendDB(ex(db_extention, chain_db), block)
    else:
        print('FAILED TESTS')
        return 'bad'
def shorten_chain_db(new_length, db_ex=''):
    f=open(ex(db_ex, chain_db), 'r')
    lines = f.readlines()
    f.close()
    f = open(ex(db_ex, chain_db),"w")
    i=0
    for line in lines:
        a=line2dic(line)
        if a['length']<new_length:# and a['length']>new_length-1500:
            f.write(line)
    f.close()
def chain_unpush(db_ex=''):
    chain=load_chain(db_ex)
    orphaned_txs=[]
    txs=load_transactions(db_ex)
    state=state_library.current_state(db_ex)
    length=state['length']
    state=state_library.recent_backup(db_ex)
    for i in range(length-state['length']):
        try:
            orphaned_txs+=chain[-1-i]['transactions']
        except:
            pass
#    chain=chain[:-1]
    #reset_chain() instead, just back up to the nearest save.
    shorten_chain_db(state['length'], db_ex)
    state_library.save_state(state, db_ex)
    reset_transactions(db_ex)
#    for i in chain[-100:]:
#        chain_push(i)
    add_transactions(orphaned_txs, db_ex)
    add_transactions(txs, db_ex)
count_value=0
count_timer=time.time()-60
def probability(p, func):
    if random.random()<p:
        return func
def getblockcount():
    global count_value
    global count_timer
    if time.time()-count_timer<60:
        return count_value
    try:
        peer='http://blockexplorer.com/q/getblockcount'
        URL=urllib.urlopen(peer)
        URL=URL.read()
        count_value=int(URL)
    except:
        peer='http://blockchain.info/q/getblockcount'
        URL=urllib.urlopen(peer)
        URL=URL.read()
        count_value=int(URL)
    count_timer=time.time()
    return count_value
hash_dic={}
def getblockhash(count):
    global hash_dic
    if str(count) in hash_dic:
        return hash_dic[str(count)]
    try:
        peer='http://blockexplorer.com/q/getblockhash/'+str(count)
        URL=urllib.urlopen(peer)
        URL=URL.read()
        int(URL, 16)
        hash_dic[str(count)]=URL
        return URL
    except:
        peer='http://blockchain.info/q/getblockhash/'+str(count)
        URL=urllib.urlopen(peer)
        URL=URL.read()
        int(URL, 16)
        hash_dic[str(count)]=URL
        return URL

def package(dic):
    return json.dumps(dic).encode('hex')
def unpackage(dic):
    try:
        return json.loads(dic.decode('hex'))
    except:
        error('here')
def difficulty(bitcoin_count, leng):
    def buffer(s, n):
        while len(s)<n:
            s='0'+s
        return s
    try:
        hashes_required=int((10**60)*((9.0/10)**(float(bitcoin_count)-float(genesisbitcoin)-(float(leng)/10)))+1)#for bitcoin
#    hashes_required=int((10**60)*((9.0/10)**(float(bitcoin_count)-float(genesisbitcoin)-(float(leng)/2.5)))+1)#for litcoin
#    hashes_required=int((10**60)*((9.0/10)**(float(bitcoin_count)-float(genesisbitcoin)-(float(leng)/25)))+1)#for laziness, every 6 seconds??
    except:
        hashes_required=999999999999999999999999999999999999999999999999999999999999
    out=buffer(hex(int('f'*64, 16)/hashes_required)[2:], 64)
    return out
def blockhash(chain_length, nonce, state, transactions, bitcoin_hash):
    fixed_transactions=[]
    if len(transactions)==0:
        error('here')
    for i in transactions:
        new=''
        for key in sorted(i.keys()):
            new=new+str(key)+':'+str(i[key])+','
        fixed_transactions.append(new)
    exact=str(chain_length)+str(nonce)+str(state['recent_hash'])+str(sorted(fixed_transactions))+str(bitcoin_hash)
#    return {'hash':pt.sha256(exact), 'exact':exact}
    return {'hash':pt.sha256(exact)}
def reverse(l):
    out=[]
    while l != []:
        out=[l[0]]+out
        l=l[1:]
    return out
def new_block_check(block, state):
    def f(x):
        return str(block[x])
    if 'length' not in block or 'bitcoin_count' not in block or 'transactions' not in block:
        print('ERRROR !')
        return False
    diff=difficulty(f('bitcoin_count'), f('length'))
    ver=verify_transactions(block['transactions'], state)
    if not ver['bool']:
        print('44')
        return False
#    print('new_ block: ' +str(block))
    if f('sha') != blockhash(f('length'), f('nonce'), state, block['transactions'], f('bitcoin_hash'))['hash']:
        print('blockhash: ' +str(blockhash(f('length'), f('nonce'), state, block['transactions'], f('bitcoin_hash'))))
        print('block invalid because blockhash was computed incorrectly')
#        error('here')
        return False
    a=getblockcount()
    if int(f('bitcoin_count'))>int(a):
        print('website: ' + str(type(a)))
        print('f: ' +str(type(f('bitcoin_count'))))
        print('COUNT ERROR')
        return False
    elif f('sha')>diff:
        print('block invalid because blockhash is not of sufficient difficulty')
        return False
    elif f('bitcoin_hash')!=getblockhash(int(f('bitcoin_count'))):
        print('bitcoin _hash: ' +f('bitcoin_hash'))
        print('bitcoin_count: ' +f('bitcoin_count'))
        print('blockhash: ' +str(getblockhash(int(f('bitcoin_count')))))
        print('block invalid because it does not contain the correct bitcoin hash')
        error('here')
        return False
    elif f('prev_sha')!=state['recent_hash']:
        print('block invalid because it does not contain the previous block\'s hash')
        return False
    return True

def verify_transactions(txs, state):
    txs=copy.deepcopy(txs)
    if len(txs)==0:
        return {'bool':True, 'newstate':state}
    print('txs: ' +str(txs))
    length=len(txs)
    state=copy.deepcopy(state)
    remove_list=[]
    for i in txs:#maybe this should be sorted
        (state, booll) = message.attempt_absorb(i, state)
        if booll:
            remove_list.append(i)
    for i in remove_list:
        txs.remove(i)
    if len(txs)>=length:
        print('HERE')
        print(txs)
        return {'bool':False}
    if len(txs)==0:
        return {'bool':True, 'newstate':state}
    else:
        return verify_transactions(txs, state)

def send_command(peer, command):
#    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    command['version']=settings.version
    url=peer.format(package(command))
    print('in send command')
    time.sleep(1)#so we don't DDOS the networking computers which we all depend on.
    if 'onion' in url:
        try:
            print('trying privoxy method')
            proxy_support = urllib2.ProxyHandler({"http" : "127.0.0.1:8118"})
            opener = urllib2.build_opener(proxy_support) 
            out=opener.open(url)
            out=out.read()
            print('privoxy succeeded')
        except:
            print('url: ' +str(url))
            out={'error':'cannot connect to peer'}
    else:
        try:
            print('attempt to open: ' +str(url))
            URL=urllib.urlopen(url)
            out=URL.read()
        except:
            print('url: ' +str(url))
            out={'error':'cannot connect to peer'}
    try:
        return unpackage(out)
    except:
        return out
def mine_1(reward_pubkey, peers, times, db_extention):
    #got to add extention onto all the database names.
    sha={'hash':100}
    diff=0
    hash_count=0
    print('start mining ' +str(times)+ ' times')
    while sha['hash']>diff:
#        print(str(hash_count))
        if hash_count>=times:
#            time.sleep(2)#otherwise you send requests WAY TOO FAST and the networking miners shutdown.
            print('was unable to find blocks')
            return False
        state=state_library.current_state(db_extention)
        bitcoin_count=getblockcount()
        bitcoin_hash=getblockhash(bitcoin_count)
        diff=difficulty(bitcoin_count, state['length']+1)
        nonce=random.randint(0,10000000000000000)
#        time.sleep(0.01)
        transactions=load_transactions(db_extention)
        extra=0
        for tx in transactions:
            if tx['id']==reward_pubkey:
                extra+=1
        if reward_pubkey not in state:
            state[reward_pubkey]={'count':1, 'amount':0}
        if 'count' not in state[reward_pubkey]:
            state[reward_pubkey]['count']=1
        count=state[reward_pubkey]['count']+extra
        transactions.append({'type':'mint', 'amount':10**5, 'id':reward_pubkey, 'count':count})
        length=state['length']
        sha=blockhash(length, nonce, state, transactions, bitcoin_hash)
        hash_count+=1
#    block={'nonce':nonce, 'length':length, 'sha':sha['hash'], 'transactions':transactions, 'bitcoin_hash':bitcoin_hash, 'bitcoin_count':bitcoin_count, 'exact':sha['exact'], 'prev_sha':state['recent_hash']}
    block={'nonce':nonce, 'length':length, 'sha':sha['hash'], 'transactions':transactions, 'bitcoin_hash':bitcoin_hash, 'bitcoin_count':bitcoin_count, 'prev_sha':state['recent_hash']}
    print('new link: ' +str(block))
    chain_push(block, db_extention)
#    pushblock(block, peers)
def mine(reward_pubkey, peers, hashes_till_check, db_extention=''):
    while True:
        peer_check_all(peers, db_extention)
        if hashes_till_check>0:
            mine_1(reward_pubkey, peers, hashes_till_check, db_extention)
        if db_extention=='':
            a=load_appendDB('suggested_transactions.db')
            add_transactions(a)
            reset_appendDB('suggested_transactions.db')
            a=load_appendDB('suggested_blocks.db')
            for block in a:
                chain_push(block)
            reset_appendDB('suggested_blocks.db')
        else:
            peer_check_all(peers, db_extention)
            peer_check_all(peers, db_extention)
            peer_check_all(peers, db_extention)
            
def fork_check(newblocks, state):#while we are mining on a forked chain, this check returns True. once we are back onto main chain, it returns false.
    try:
#        hashes=filter(lambda x: 'prev_sha' in x and x['prev_sha']==state['recent_hash'], newblocks)
        hashes=filter(lambda x: 'sha' in x and x['sha']==state['recent_hash'], newblocks)
    except:
        error('here')
    return len(hashes)==0

def peer_check_all(peers, db_extention):
    blocks=[]
    for peer in peers:
        blocks+=peer_check(peer, db_extention)
    for block in blocks:
        print('$$$$$$$$$$$$$')
        chain_push(block, db_extention)

def pushtx(tx, peers):
    for p in peers:
        send_command(p, {'type':'pushtx', 'tx':tx})

def pushblock(block, peers):
    for p in peers:
        send_command(p, {'type':'pushblock', 'block':block})    
def set_minus(l1, l2, ids):#l1-l2
    out=[]
    def member_of(a, l, ids):
        for i in l:
            if a[ids[0]]==i[ids[0]] and a[ids[1]]==i[ids[1]]:
                return True
        return False
    for i in l1:
        if not member_of(i, l2, ids):
            out.append(i)
    return out

def peer_check(peer, db_ex):
    print('checking peer')
    state=state_library.current_state(db_ex)
    cmd=(lambda x: send_command(peer, x))
    block_count=cmd({'type':'blockCount'})
    print('block count: ' +str(block_count))
    if type(block_count)!=type({'a':1}):
        return []
    if 'error' in block_count.keys():
        return []        
    print('state: ' +str(state))
    ahead=int(block_count['length'])-int(state['length'])
    if ahead < 0:
        chain=copy.deepcopy(load_chain(db_ex))
        print('len chain: ' +str(len(chain)))
        print('length: ' +str(int(block_count['length'])+1))
        print('state len: ' +str(state['length']))
        try:
            pushblock(chain[int(block_count['length'])+1],[peer])
        except:
            pass
        probability(0.2, chain_unpush(db_ex))
        return []
    if ahead == 0:#if we are on the same block, ask for any new txs
        print('ON SAME BLOCK')
        if state['recent_hash']!=block_count['recent_hash']:
            chain_unpush(db_ex)
            print('WE WERE ON A FORK. time to back up.')
            return []
        my_txs=load_transactions(db_ex)
        txs=cmd({'type':'transactions'})
        add_transactions(txs, db_ex)
        pushers=set_minus(my_txs, txs, ['count', 'id'])
        for push in pushers:
            pushtx(push, [peer])
        return []
#    if ahead>1001:
#        try_state=cmd({'type':'backup_states',
#                   'start': block_count['length']-1000})
#        if type(try_state)==type({'a':'1'}) and 'error' not in state:
#            print('state: ' +str(state))
#            state=try_state
#            state_library.save_state(state)
#        return []
    print("############################## ahead: "+str(ahead))
    def f():
        for i in range(5):
            chain_unpush(db_ex)
    probability(0.03, chain_unpush(db_ex))
    start=int(state['length'])-30
    if start<0:
        start=0
    if ahead>500:
        end=int(state['length'])+499
    else:
        end=block_count['length']
    blocks= cmd({'type':'rangeRequest', 
                 'range':[start, end]})
    print('@@@@@@@@@@@@downloaded blocks')
    if type(blocks)!=type([1,2]):
        return []
    times=1
    while fork_check(blocks, state) and times>0:
        times-=1
        chain_unpush(db_ex)
    return blocks
