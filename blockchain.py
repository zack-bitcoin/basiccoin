import time, leveldb, copy, custom, tools, stackDB, networking
import pybitcointools as pt
DB=leveldb.LevelDB('DB.db')
def db_get (n): 
    try:
        return tools.unpackage(DB.Get(str(n)))
    except:
        print('failed with key: ' + str(n))
        error('here')
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
        if tx['type'] not in boolean.keys(): 
            print('caps')
            return False
        if not verify_count(tx, txs): 
            print('abc')
            return False
        if len(tools.package(txs+[tx]))>networking.MAX_MESSAGE_SIZE+5000:
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
target='00008'+'f'*59
def adjust_amount(pubkey, amount):
    acc=db_get(pubkey)
    acc['amount']+=amount
    db_put(pubkey, acc)        
def adjust_count(pubkey, upward=True):
    acc=db_get(pubkey)
    acc['count']+=1
    db_put(pubkey, acc)
def add_block(block):
    print('add_block: '+str(block))
    def block_check(block):
        #never allow userid 'txs_backup' or 'txs'
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
        if tools.det_hash(block)>target: 
            print('11')
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
        adjust_amount(tx['to'], tx['amount'])
        adjust_count(tx['id'])
    update={'mint':mint, 'spend':spend}
    if block_check(block):
        db_put(block['length'], block)
        stackDB.set_length(block['length'])
        stackDB.reset_txs()
        try:
            stackDB.set_hash(tools.det_hash(db_get(block['length']-1)))
        except:
            stackDB.set_hash(tools.det_hash(0))
        for tx in block['txs']:
            update[tx['type']](tx)
#    else:
#        error('here')
    #update state about the new txs
    #create a backup        
#        DB.Put(txid(tx), package({'tx':tx, 'status':'unspent'}))
def delete_block():
    def mint(tx):
        adjust_amount(tx['id'], -custom.block_reward)
        adjust_count(tx['id'], False)
    def spend(tx):
        adjust_amount(tx['id'], tx['amount'])
        adjust_amount(tx['to'], -tx['amount'])
        adjust_count(tx['id'], False)
    length=stackDB.current_length()
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
