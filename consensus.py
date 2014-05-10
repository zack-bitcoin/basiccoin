import blockchain, custom, tools, networking, random, time, copy
#This file mines blocks and talks to peers. It maintains consensus of the blockchain.
def mine(hashes_till_check, reward_address, DB):
    #tries to mine the next block hashes_till_check many times.
    def make_mint(pubkey, DB): 
        address=tools.make_address([reward_address], 1)
        return {'type':'mint', 'id':[pubkey], 'signature':['first_sig'],
                'count':blockchain.count(address, DB)}
                                       
    def genesis(pubkey, DB):
        target=blockchain.target(DB)
        out={'version':custom.version,
             'length':0,
             'time':time.time(),
             'target':target,
             'diffLength':blockchain.hexInvert(target),
             'txs':[make_mint(pubkey, DB)]}
        out=tools.unpackage(tools.package(out))
        return out
        
    def make_block(prev_block, txs, pubkey, DB):
        leng=int(prev_block['length'])+1
        target=blockchain.target(DB, leng)
        diffLength=blockchain.hexSum(prev_block['diffLength'], 
                                     blockchain.hexInvert(target))
        out={'version':custom.version,
             'txs':txs+[make_mint(pubkey, DB)],
             'length':leng,
             'time':time.time(),
             'diffLength':diffLength,
             'target':target,
             'prevHash':tools.det_hash(prev_block)}
        out=tools.unpackage(tools.package(out))
        return out
        
    def POW(block, hashes, target):
        halfHash=tools.det_hash(block)
        block[u'nonce']=random.randint(0,100000000000000000)
        count=0
        while tools.det_hash({u'nonce':block['nonce'], 
                              u'halfHash':halfHash})>target:
            count+=1
            block[u'nonce']+=1
            if count>hashes:
                return {'error':False}
            ''' for testing sudden loss in hashpower from miners.
            if block[u'length']>150:
            else: time.sleep(0.01)
            '''
        return block
        
    length=copy.deepcopy(DB['length'])
    if length==-1:
        block=genesis(reward_address, DB)
        txs=[]
    else:
        prev_block=blockchain.db_get(length, DB)
        txs=DB['txs']
        block=make_block(prev_block, txs, reward_address, DB)
    block=POW(block, hashes_till_check, blockchain.target(DB, block['length']))
    DB['suggested_blocks'].append(block)

def peers_check(peers, DB):
    #check on the peers to see if they know about more blocks than we do.
    def fork_check(newblocks, DB):
        #if we are on a fork, return True
        #try:
        length=copy.deepcopy(DB['length'])
        block=blockchain.db_get(length, DB)
        recent_hash=tools.det_hash(block)
        their_hashes=map(tools.det_hash, newblocks)
        return recent_hash not in map(tools.det_hash, newblocks)
        #except Exception as e:
            #print('ERROR: ' +str(e))
         #   return False
            
    def peer_check(peer, DB):
        cmd=(lambda x: networking.send_command(peer, x))
        block_count=cmd({'type':'blockCount'})
        if type(block_count)!=type({'a':1}):
            return 
        if 'error' in block_count.keys():
            return         
        length=copy.deepcopy(DB['length'])
        us=copy.deepcopy(DB['diffLength'])
        them=block_count['diffLength']
        ahead=length-block_count['length']
        if them < us and ahead>0:#if we are ahead of them
            cmd({'type':'pushblock', 
                 'block':blockchain.db_get(block_count['length']+1, DB)})
            return []
        if length<0: return []
        if us == them:#if we are on the same block, ask for any new txs
            block=blockchain.db_get(length, DB)
            if 'recent_hash' in block_count:
                if tools.det_hash(block)!=block_count['recent_hash']:
                    blockchain.delete_block()
                    #print('WE WERE ON A FORK. time to back up.')
                    return []
            my_txs=DB['txs']
            txs=cmd({'type':'txs'})
            for tx in txs:
                DB['suggested_txs'].append(tx)
            pushers=[x for x in my_txs if x not in txs]
            for push in pushers:
                cmd({'type':'pushtx', 'tx':push})
            return []
        start=length-2
        if start<0:
            start=0
        if ahead>custom.download_many:
            end=length+custom.doanload_many-1
        else:
            end=block_count['length']
        blocks= cmd({'type':'rangeRequest', 
                     'range':[start, end]})
        if type(blocks)!=type([1,2]):
            return []
        times=2
        while fork_check(blocks, DB) and times>0:
            times-=1
            blockchain.delete_block(DB)
        for block in blocks:
            DB['suggested_blocks'].append(block)
            
    for peer in peers:
        peer_check(peer, DB)

def suggestions(DB):
    #the other thread called listener.server is listening to peers and adding 
    #suggested transactions and blocks from them into these lists of 
    #suggestions. 
    for tx in DB['suggested_txs']:
        #print('SUGGESTED TX')
        #print('tx: ' +str(tx))
        blockchain.add_tx(tx, DB)
    #[blockchain.add_tx(tx, DB) for tx in DB['suggested_txs']]
    [blockchain.add_block(block, DB) for block in DB['suggested_blocks']]
    DB['suggested_txs']=[]
    DB['suggested_blocks']=[]

def mainloop(reward_address, peers, hashes_till_check, DB):
    while True:
        #mine(hashes_till_check, reward_address, DB) 
        time.sleep(1)
        peers_check(peers, DB)
        suggestions(DB)

def miner(reward_address, peers, hashes_till_check, DB):
    while True: 
        mine(hashes_till_check, reward_address, DB)

