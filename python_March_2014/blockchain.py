""" This file explains explains the rules for adding and removing blocks from the local chain.
"""
import time
import copy
import custom
import networking
import transactions
import tools
import target
import database


def add_tx(tx, DB={}):
    # Attempt to add a new transaction into the pool.
    #print('top of add_tx')
    out=['']
    if type(tx) != type({'a':1}): 
        return False
    address = tools.make_address(tx['pubkeys'], len(tx['signatures']))
    def verify_count(tx, txs):
        return tx['count'] != tools.count(address, DB)
    def type_check(tx, txs):
        if not tools.E_check(tx, 'type', [str, unicode]):
            out[0]+='blockchain type'
            return False
        if tx['type'] == 'mint':
            return False
        if tx['type'] not in transactions.tx_check:
            out[0]+='bad type'
            return False
        return True
    def too_big_block(tx, txs):
        return len(tools.package(txs+[tx])) > networking.MAX_MESSAGE_SIZE - 5000
    def verify_tx(tx, txs, out):
        if not type_check(tx, txs):
            out[0]+='type error'
            return False
        if tx in txs:
            out[0]+='no duplicates'
            return False
        if verify_count(tx, txs):
            out[0]+='count error'
            return False
        if too_big_block(tx, txs):
            out[0]+='too many txs'
            return False
        if not transactions.tx_check[tx['type']](tx, txs, out, DB):
            out[0]+= 'tx: ' + str(tx)
            return False
        return True
    #tools.log('attempt to add tx: ' +str(tx))
    T=tools.db_get('txs')
    if verify_tx(tx, T, out):
        T.append(tx)
        tools.db_put('txs', T)
        return('added tx: ' +str(tx))
    else:
        return('failed to add tx because: '+out[0])
def recent_blockthings(key, size, length=0):
    storage = tools.db_get(key)
    def get_val(length):
        leng = str(length)
        if not leng in storage:            
            block=tools.db_get(leng)
            if block==database.default_entry():
                if leng==tools.db_get('length'):
                    tools.db_put('length', int(leng)-1)
                    block=tools.db_get(leng)
                else:
                    error()
            #try:
            storage[leng] = tools.db_get(leng)[key[:-1]]
            tools.db_put(key, storage)
        return storage[leng]
    def clean_up(storage, end):
        if end<0: return
        if not str(end) in storage: return
        else:
            storage.pop(str(end))
            return clean_up(storage, end-1)
    if length == 0:
        length = tools.db_get('length')
    start = max((length-size), 0)
    clean_up(storage, length-max(custom.mmm, custom.history_length)-100)
    return map(get_val, range(start, length))
def hexSum(a, b):
    # Sum of numbers expressed as hexidecimal strings
    return tools.buffer_(str(hex(int(a, 16)+int(b, 16)))[2: -1], 64)
def hexInvert(n):
    # Use double-size for division, to reduce information leakage.
    return tools.buffer_(str(hex(int('f' * 128, 16) / int(n, 16)))[2: -1], 64)
def add_block(block_pair, DB={}):
    """Attempts adding a new block to the blockchain.
     Median is good for weeding out liars, so long as the liars don't have 51%
     hashpower. """
    def median(mylist):
        if len(mylist) < 1:
            return 0
        return sorted(mylist)[len(mylist) / 2]

    def block_check(block, DB):
        def log_(txt): pass #return tools.log(txt)
        def tx_check(txs):
            start = copy.deepcopy(txs)
            out = []
            start_copy = []
            while start != start_copy:
                if start == []:
                    return False  # Block passes this test
                start_copy = copy.deepcopy(start)
                if transactions.tx_check[start[-1]['type']](start[-1], out, [''], DB):
                    out.append(start.pop())
                else:
                    return True  # Block is invalid
            return True  # Block is invalid
        if not isinstance(block, dict): return False
        if 'error' in block: return False
        if not tools.E_check(block, 'length', [int]):
            log_('no length')
            return False
        length =tools.db_get('length')
        if type(block['length'])!=type(1): 
            log_('wrong length type')
            return False
        if int(block['length']) != int(length) + 1:
            log_('wrong longth')
            return False
        if block['diffLength'] != hexSum(tools.db_get('diffLength'),
                                         hexInvert(block['target'])):
            log_('diflength error')
            return False
        if length >= 0:
            if tools.det_hash(tools.db_get(length, DB)) != block['prevHash']:
                log_('det hash error')
                return False
        if u'target' not in block.keys():
            log_('target error')
            return False
        half_way=tools.make_half_way(block)
        if tools.det_hash(half_way) > block['target']:
            log_('det hash error 2')
            return False
        if block['target'] != target.target(block['length']):
            log_('block: ' +str(block))
            log_('target: ' +str(target.target(block['length'])))
            log_('wrong target')
            return False
        earliest = median(recent_blockthings('times', custom.mmm))
        if 'time' not in block: 
            log_('no time')
            return False
        if block['time'] > time.time()+60*6: 
            log_('too late')
            return False
        if block['time'] < earliest: 
            log_('too early')
            return False
        if tx_check(block['txs']): 
            log_('tx check')
            return False
        return True
    if type(block_pair)==type([1,2,3]):
        block=block_pair[0]
        peer=block_pair[1]
    else:
        block=block_pair
        peer=False
    #tools.log('attempt to add block: ' +str(block))
    if block_check(block, DB):
        #tools.log('add_block: ' + str(block))
        tools.db_put(block['length'], block, DB)
        tools.db_put('length', block['length'])
        tools.db_put('diffLength', block['diffLength'])
        orphans = tools.db_get('txs')
        tools.db_put('txs', [])
        for tx in block['txs']:
            transactions.update[tx['type']](tx, DB, True)
        for tx in orphans:
            add_tx(tx, DB)
        #while tools.db_get('length')!=block['length']:
        #    time.sleep(0.0001)

def delete_block(DB):
    """ Removes the most recent block from the blockchain. """
    length=tools.db_get('length')
    if length < 0:
        return
    try:
        ts=tools.db_get('targets')
        ts.pop(str(length))
        tools.db_put('targets', ts)
    except:
        pass
    try:
        ts=tools.db_get('times')
        ts.pop(str(length))
        tools.db_put('times', ts)
    except:
        pass
    block = tools.db_get(length, DB)
    orphans = tools.db_get('txs')
    tools.db_put('txs', [])
    for tx in block['txs']:
        orphans.append(tx)
        tools.db_put('add_block', False)
        transactions.update[tx['type']](tx, DB, False)
    tools.db_delete(length, DB)
    length-=1
    tools.db_put('length', length)
    if length == -1:
        tools.db_put('diffLength', '0')
    else:
        block = tools.db_get(length, DB)
        tools.db_put('diffLength', block['diffLength'])
    for orphan in sorted(orphans, key=lambda x: x['count']):
        add_tx(orphan, DB)
    #while tools.db_get('length')!=length:
    #    time.sleep(0.0001)
def f(blocks_queue, txs_queue):
    def bb(): return blocks_queue.empty()
    def tb(): return txs_queue.empty()
    def ff(queue, g, b, s):
        while not b():
            time.sleep(0.0001)
            try:
                g(queue.get(False))
            except Exception as exc:
                tools.log('suggestions ' + s)
                tools.log(exc)
    while True:
        time.sleep(0.1)
        if tools.db_get('stop'):
            tools.dump_out(blocks_queue)
            tools.dump_out(txs_queue)
            return
        while not bb() or not tb():
            ff(blocks_queue, add_block, bb, 'block')
            ff(txs_queue, add_tx, tb, 'tx')
import cProfile
def main(DB): return f(DB["suggested_blocks"], DB["suggested_txs"])
def profile(DB):
    import pprint
    p=cProfile.Profile()
    p.run('blockchain.main(custom.DB)')
    g=p.getstats()
    #g=g.sorted(lambda x: x.inlinetime)
    g=sorted(g, key=lambda x: x.totaltime)
    g.reverse()
    pprint.pprint(g)
    #return f(DB['suggested_blocks'], DB['suggested_txs'])
    
