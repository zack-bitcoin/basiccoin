import blockchain, custom, tools, networking, random, time, copy
#This file mines blocks and talks to peers. It maintains consensus of the blockchain.
def mine(hashes_till_check, reward_address, DB):
    #tries to mine the next block hashes_till_check many times.
    def make_mint(pubkey, DB): 
        address=tools.make_address([reward_address], 1)
        return {'type':'mint', 'pubkeys':[pubkey], 'signatures':['first_sig'],
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
        
    length=DB['length']
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
    def peer_check(peer, DB):

        def cmd(x): return networking.send_command(peer, x)

        def download_blocks(peer, DB, peers_block_count, length):

            def fork_check(newblocks, DB):
                length=copy.deepcopy(DB['length'])
                block=blockchain.db_get(length, DB)
                recent_hash=tools.det_hash(block)
                their_hashes=map(tools.det_hash, newblocks)
                return recent_hash not in map(tools.det_hash, newblocks)

            def bounds(length, peers_block_count, DB):
                if peers_block_count['length']-length>custom.download_many:
                    end=length+custom.download_many-1
                else:
                    end=peers_block_count['length']
                return [max(length-2, 0), end]

            blocks= cmd({'type':'rangeRequest',
                    'range':bounds(length, peers_block_count, DB)})
            if type(blocks)!=type([1,2]): return []
            for i in range(2):#only delete a max of 2 blocks, otherwise a 
                #peer might trick us into deleting everything over and over.
                if fork_check(blocks, DB):
                    blockchain.delete_block(DB)
            for block in blocks:
                DB['suggested_blocks'].append(block)
            return

        def ask_for_txs(peer, DB):
            txs=cmd({'type':'txs'})
            for tx in txs:
                DB['suggested_txs'].append(tx)
            pushers=[x for x in DB['txs'] if x not in txs]
            for push in pushers:
                cmd({'type':'pushtx', 'tx':push})
            return []

        def give_block(peer, DB, block_count):
            cmd({'type':'pushblock', 
                 'block':blockchain.db_get(block_count['length']+1,
                                           DB)})
            return []

        block_count=cmd({'type':'blockCount'})
        if type(block_count)!=type({'a':1}):
            return
        if 'error' in block_count.keys():
            return
        length=DB['length']
        us=DB['diffLength']
        them=block_count['diffLength']
        if them < us: return give_block(peer, DB, block_count)
        if us == them: return ask_for_txs(peer, DB)
        return download_blocks(peer, DB, block_count, length)

    for peer in peers:
        peer_check(peer, DB)

def suggestions(DB):
    [blockchain.add_tx(tx, DB) for tx in DB['suggested_txs']]
    DB['suggested_txs']=[]
    [blockchain.add_block(block, DB) for block in DB['suggested_blocks']]
    DB['suggested_blocks']=[]

def mainloop(reward_address, peers, hashes_till_check, DB):
    while True:
        time.sleep(1)
        peers_check(peers, DB)
        suggestions(DB)

def miner(reward_address, peers, hashes_till_check, DB):
    while True: 
        mine(hashes_till_check, reward_address, DB)
