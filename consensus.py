import blockchain, custom, tools, networking, stackDB, random, time
#This file mines blocks and talks to peers. It maintains consensus of the blockchain.
def mine(hashes_till_check, reward_address, DB):
    def make_mint(pubkey, DB): return {'type':'mint', 'id':pubkey, 'count':blockchain.count(pubkey, DB)}
    def genesis(pubkey, DB):
        out={'version':custom.version,
             'length':0,
             'time':time.time(),
             'target':blockchain.target(DB),
             'txs':[make_mint(pubkey, DB)]}
        out=tools.unpackage(tools.package(out))
        return out
    def make_block(prev_block, txs, pubkey, DB):
        leng=int(prev_block['length'])+1
        out={'version':custom.version,
             'txs':txs+[make_mint(pubkey, DB)],
             'length':leng,
             'time':time.time(),
             'target':blockchain.target(DB),
             'prevHash':tools.det_hash(prev_block)}
        out=tools.unpackage(tools.package(out))
        return out
    def POW(block, hashes, target):
        halfHash=tools.det_hash(block)
        block[u'nonce']=random.randint(0,100000000000000000)
        count=0
        while tools.det_hash({u'nonce':block['nonce'], u'halfHash':halfHash})>target:
            count+=1
            block[u'nonce']+=1
            if count>hashes:
                return {'error':False}
            ''' for testing sudden loss in hashpower from miners.
            if block[u'length']>150:# and block[u'nonce']%10==0: time.sleep(0.1)
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
    stackDB.push('suggested_blocks.db', block)
def peers_check(peers, DB):
    def fork_check(newblocks, DB):
        #if we are on a fork, return True
        try:
            length=DB['length']
            block=blockchain.db_get(length, DB)
            recent_hash=tools.det_hash(block)
            return recent_hash not in map(tools.det_hash, newblocks)
        except Exception as e:
            #print('ERROR: ' +str(e))
            return False
    def peer_check(peer, DB):
        cmd=(lambda x: networking.send_command(peer, x))
        block_count=cmd({'type':'blockCount'})
        if type(block_count)!=type({'a':1}):
            return 
        if 'error' in block_count.keys():
            return         
        length=DB['length']
        ahead=int(block_count['length'])-length
        if ahead < 0:#if we are ahead of them
            cmd({'type':'pushblock', 'block':blockchain.db_get(block_count['length']+1, DB)})
            return []
        if ahead == 0:#if we are on the same block, ask for any new txs
            block=blockchain.db_get(length, DB)
            if 'recent_hash' in block_count and tools.det_hash(block)!=block_count['recent_hash']:
                blockchain.delete_block()
                #print('WE WERE ON A FORK. time to back up.')
                return []
            my_txs=DB['txs']
            txs=cmd({'type':'txs'})
            for tx in txs:
                stackDB.push('suggested_txs.db', tx)
            pushers=[x for x in my_txs if x not in txs]
            for push in pushers:
                cmd({'type':'pushtx', 'tx':push})
            return []
        start=length-30
        if start<0:
            start=0
        if ahead>500:
            end=length+499
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
            stackDB.push('suggested_blocks.db', block)
    for peer in peers:
        peer_check(peer, DB)
def suggestions(DB):
    def file_map(func, file):
        things=stackDB.load(file)
        stackDB.reset(file)
        [func(x, DB) for x in things]
    map(file_map, [blockchain.add_tx, blockchain.add_block], ['suggested_txs.db', 'suggested_blocks.db'])
    stackDB.reset('suggested_blocks.db')
    stackDB.reset('suggested_txs.db')
def mainloop(reward_address, peers, hashes_till_check, DB):
    while True:
        mine(hashes_till_check, reward_address, DB) 
        peers_check(peers, DB)
        suggestions(DB)


