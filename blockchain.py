import time, leveldb, copy, custom, tools, stackDB, networking
import pybitcointools as pt
DB=leveldb.LevelDB('DB.db')
def db_get (n): 
    try:
        a=DB.Get(str(n))
    except:
        error('here')
    return tools.unpackage(a)
def db_put(key, dic): return DB.Put(str(key), tools.package(dic))
def db_delete(key): return DB.delete(str(key))
def count(pubkey):
    c=0
    try:
        txs=stackDB.current_txs()
    except:
        stackDB.reset_txs()
        txs=[]
    for t in txs:
        if pubkey==t['id']:
            c+=1
    try:
        acc=db_get(pubkey)
    except:
        acc={'count':0, 'amount':0}
        db_put(pubkey, acc)
    return acc['count']+c
def add_tx(tx):
    def verify_count(tx, txs): return tx['count']==count(tx['id'])
    def spend_verify(tx, txs): 
        try:
            if not pt.ecdsa_verify(tools.det_hash(tx, keys), tx['signature'], db_get(tx['id'])['pubkey']): 
                print('Qwerty')
                return False
            return db_get(tx['id'])['amount']>tx['amount']+custom.fee
        except:
            print('ase')
            return False
    def mint_verify(tx, txs):
        for t in txs:#ensures 1 mint per block.
            if t['type']=='mint': 
                print('aa')
                return False
        return True
    def verify_tx(tx, txs):
        boolean={'spend':spend_verify, 'mint':mint_verify}
        if type(tx) != type({'a':1}) or 'type' not in tx:
            print('type error')
            return False
        if tx['type'] not in boolean.keys(): 
            print('caps')
            return False
        if not verify_count(tx, txs): 
            print('abc')
            return False
        if len(tools.package(txs+[tx]))>networking.MAX_MESSAGE_SIZE-5000:
            #change 5000 a number bigger than the size of the rest of the block
            #maybe 5000 not needed, if block and txs are sent as different messages.
            print('maxed out zeroth confirmation txs')
            return False
        return boolean[tx['type']](tx, txs)
    txs=stackDB.current_txs()
    if verify_tx(tx, txs):
        stackDB.add_tx(tx)
        return True
    else:
        print('tx did not get added')
        return False
targets={}
times={}#stores blocktimes
def recent_blockthings(key, size=100, length=0):
    storage={}
    if key=='time': storage=times
    if key=='target': storage=targets
    def get_val(length):
        leng=str(length)
        if not leng in storage:
            storage[leng]=db_get(leng)[key]
        return storage[leng]
    if length==0: length=stackDB.current_length()
    f=lambda x: [get_val(y) for y in x]
    try:
        return f(range(length-size, length))
    except:
        return f(range(0, length))
def target(length=0):
#    def detensify(frac, m): return (frac/m+(m-1.0)/m) #brings frac closer to the value 1 by a factor of m
#    inflection=0.977159968#This constant is selected such that the 30 most recent blocks count for 1/2 the total weight.
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
    def estimate_target():
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
        targets=recent_blockthings('target', 400)        
        for i in range(len(targets)):
            targets[i]=invert(targets[i])#invert because target is proportional to 1/(# hashes required to mine a block on average)
        w=weights(inflection, len(targets))
        total_weight=sum(w)
        weighted_targets=[multiply_blocktime(targets[i], w[i]/total_weight) for i in range(len(targets))]
        return invert(acc(plus, weighted_targets))
    def estimate_time():
        data=[]
        for x in recent_blockthings('time', 400):
            try:
                data.append(x-prev_x)
            except:
                pass
            prev_x=x
        w=weights(inflection, len(data))
        tw=sum(w)
        return sum([w[i]*data[i]/tw for i in range(len(data))])
    if length==0 or length==stackDB.current_length()+1: 
        length=stackDB.current_length()+1
    else:#we calculated this before
        return targets[str(length)]
    if length<10:
        return buffer('f'*62)
    e=estimate_time()
    f=estimate_target()
    return multiply_blocktime(f, e/custom.blocktime(length))
def adjust_amount(pubkey, amount):
    acc=db_get(pubkey)
    acc['amount']+=amount
    db_put(pubkey, acc)        
def adjust_count(pubkey, upward=True):
    acc=db_get(pubkey)
    acc['count']+=1
    db_put(pubkey, acc)
def add_block(block):
    def median(mylist): #median is good for weeding out liars, so long as the liars don't have 51% hashpower.
        if len(mylist)<1: return 0
        return sorted(mylist)[len(mylist) / 2]
    def block_check(block):
        earliest=median(recent_blockthings('time'))
        length=stackDB.current_length()
        if type(block)!=type({'a':1}):
            print('34')
            return False
        if int(block['length'])!=int(length)+1: 
            print(block['length'])
            print(length)
            print('12')
            return False
        if length >=0 and tools.det_hash(db_get(length))!=block['prevHash']: 
            print('22')
            return False
        if 'target' not in block.keys() or tools.det_hash(block)>block['target'] or block['target']!=target(block['length']):
            print('11')
            return False
        if 'time' not in block or block['time']>time.time() or block['time']<earliest:
            print('2323')
            return False
        backup=stackDB.current_txs()
        stackDB.reset_txs()
        mints=0
        for tx in block['txs']:
            if tx['type']=='mint':
                mints+=1
            if not add_tx(tx) or mints>1:
                stackDB.reset_txs()
                for tx in backup:
                    add_tx(tx)
                print('overmint')
                return False
        return True
    def mint(tx):
        adjust_amount(tx['id'], custom.block_reward)
        adjust_count(tx['id'])
    def spend(tx):
        adjust_amount(tx['id'], -tx['amount'])
        adjust_amount(tx['to'], tx['amount']-custom.fee)
        adjust_count(tx['id'])
    update={'mint':mint, 'spend':spend}
    if block_check(block):
        print('add_block: '+str(block))
#        print('add_block: '+str(block['time'])+ " length: " + str(block['length']))
        db_put(block['length'], block)
        stackDB.set_length(block['length'])
        stackDB.reset_txs()
        try:
            stackDB.set_hash(tools.det_hash(db_get(block['length']-1)))
        except:
            stackDB.set_hash(tools.det_hash(0))
        for tx in block['txs']:
            update[tx['type']](tx)
def delete_block():
    print('DELETE BLOCK')
    def mint(tx):
        adjust_amount(tx['id'], -custom.block_reward)
        adjust_count(tx['id'], False)
    def spend(tx):
        adjust_amount(tx['id'], tx['amount'])
        adjust_amount(tx['to'], -tx['amount'])
        adjust_count(tx['id'], False)
    length=stackDB.current_length()
    targets.pop(str(length))
    times.pop(str(length))
    block=db_get(length)
    orphans=stackDB.current_txs()
    stackDB.reset_txs()
    stackDB.set_length(length-1)
    stackDB.set_hash(tools.det_hash(db_get(length-1)))
    downdate={'mint':mint, 'spend':spend}
    for tx in block['txs']:
        orphans.append(tx)
        downdate[tx['type']](tx)
    db_delete(length)
    for orphan in sorted(orphans, key=lambda x: x['count']):
        add_tx(tx)
