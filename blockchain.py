import time, copy, custom, tools, stackDB, networking, transactions
#this file explains how we talk to the database. It explains the rules for adding blocks and transactions.
def db_get (n, DB): 
    n=str(n)
    if len(n)==130: n=tools.pub2addr(n)
    try:
        a=DB['db'].Get(n)
    except:
        error('here')
    return tools.unpackage(a)
def db_put(key, dic, DB):  
    key=str(key)
    if len(key)==130: key=tools.pub2addr(key)
    return DB['db'].Put(key, tools.package(dic))
def db_delete(key, DB): return DB['db'].Delete(str(key))
def count(pubkey, DB):
    def zeroth_confirmation_txs(pubkey, DB):
        c=0
        try:
            txs=DB['txs']
        except:
            DB['txs']=[]
            return 0
        for t in txs:
            if pubkey==t['id']:
                c+=1
        return c
    def current(pubkey, DB):
        try:
            acc=db_get(pubkey, DB)
        except:
            acc={'count':0, 'amount':0}
            db_put(pubkey, acc, DB)
        if 'count' not in acc:
            acc['count']=0
            db_put(pubkey, acc, DB)
        return acc['count']
    return current(pubkey, DB)+zeroth_confirmation_txs(pubkey, DB)
def add_tx(tx, DB):
    def verify_count(tx, txs): return tx['count']==count(tx['id'], DB)
    def verify_tx(tx, txs):
        boolean=transactions.tx_check
        if type(tx) != type({'a':1}) or 'type' not in tx: return False
        if tx['type'] not in boolean.keys(): return False
        if not verify_count(tx, txs): return False
        if len(tools.package(txs+[tx]))>networking.MAX_MESSAGE_SIZE-5000: return False
        return boolean[tx['type']](tx, txs, DB)
    txs=DB['txs']
    if verify_tx(tx, txs):
        DB['txs'].append(tx)
    else:
        pass
        #print('tx did not get added')
targets={}
times={}#stores blocktimes
def recent_blockthings(key, DB, size=100, length=0):
    storage={}
    if key=='time': storage=times
    if key=='target': storage=targets
    def get_val(length):
        leng=str(length)
        if not leng in storage:
            storage[leng]=db_get(leng, DB)[key]
        return storage[leng]
    if length==0: length=copy.deepcopy(DB['length'])
    f=lambda x: [get_val(y) for y in x]
    try:
        return f(range(length-size, length))
    except:
        return f(range(0, length))
def target(DB, length=0):
    inflection=0.985#This constant is selected such that the 50 most recent blocks count for 1/2 the total weight.
    def buffer(str):
        if len(str)<64: return buffer('0'+str)
        return str
    def multiply_blocktime(target, number): 
        try:
            return buffer(str(hex(int(int(target, 16)*number)))[2:-1])
        except:
            return buffer('f'*62)
    def weights(inflection, length):
        out=[]
        for i in range(length):#weigh blocktimes against geometric distribution
            out.append(inflection**(length-i)) #b/c we care more about the recent blocks 
        return out
    def estimate_target(DB):
        def invert(n):
            try:
                return buffer(str(hex(int('f'*128, 16)/int(n, 16)))[2:-1])#use double-size for division, to reduce information leakage.
            except:
                return buffer('f'*62)
        def plus(a, b):
            return buffer(str(hex(int(a, 16)+int(b, 16)))[2:-1])
        def acc(func, l):
            if len(l)<1: return 0
            while len(l)>1:
                l=[func(l[0], l[1])]+l[2:]
            return l[0]
        targets=recent_blockthings('target', DB, 400)        
        for i in range(len(targets)):
            targets[i]=invert(targets[i])#invert because target is proportional to 1/(# hashes required to mine a block on average)
        w=weights(inflection, len(targets))
        total_weight=sum(w)
        weighted_targets=[multiply_blocktime(targets[i], w[i]/total_weight) for i in range(len(targets))]
        return invert(acc(plus, weighted_targets))
    def estimate_time(DB):
        data=[]
        for x in recent_blockthings('time', DB, 400):
            try:
                data.append(x-prev_x)
            except:
                pass
            prev_x=x
        w=weights(inflection, len(data))
        tw=sum(w)
        return sum([w[i]*data[i]/tw for i in range(len(data))])
    if length==0: length=DB['length']
    if length<4: return buffer('f'*60)
    if length<=DB['length']: return targets[str(length)]
    return multiply_blocktime(estimate_target(DB), estimate_time(DB)/custom.blocktime(length))
def add_block(block, DB):
    def median(mylist): #median is good for weeding out liars, so long as the liars don't have 51% hashpower.
        if len(mylist)<1: return 0
        return sorted(mylist)[len(mylist) / 2]
    def block_check(block, DB):
        earliest=median(recent_blockthings('time', DB))
        length=copy.deepcopy(DB['length'])
        if 'error' in block.keys(): return False
        if type(block)!=type({'a':1}): return False
        if int(block['length'])!=int(length)+1: return False
        if length >=0 and tools.det_hash(db_get(length, DB))!=block['prevHash']: return False
        a=copy.deepcopy(block)
        a.pop('nonce')
        if u'target' not in block.keys() or tools.det_hash({u'nonce':block['nonce'], u'halfHash':tools.det_hash(a)})>block['target'] or block['target']!=target(DB, block['length']): return False
        if 'time' not in block or block['time']>time.time() or block['time']<earliest: return False
        return True
    if block_check(block, DB):
        print('add_block: '+str(block))
        db_put(block['length'], block, DB)
        DB['length']=block['length']
        orphans=DB['txs']
        DB['txs']=[]
        for tx in block['txs']:
            transactions.update[tx['type']](tx, DB)
        for tx in orphans:
            add_tx(tx, DB)
def delete_block(DB):
    if DB['length']<0: return
    try:
        targets.pop(str(length))
        times.pop(str(length))
    except:
        pass
    block=db_get(DB['length'], DB)
    orphans=DB['txs']
    DB['txs']=[]
    for tx in block['txs']:
        orphans.append(tx)
        transactions.downdate[tx['type']](tx, DB)
    db_delete(DB['length'], DB)
    DB['length']-=1
    for orphan in sorted(orphans, key=lambda x: x['count']):
        add_tx(tx, DB)
