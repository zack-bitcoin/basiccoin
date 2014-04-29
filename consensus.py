import blockchain, custom, tools, networking, stackDB, random, time
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
        txs.append(make_mint(pubkey, DB))
        leng=int(prev_block['length'])+1
#        print('prev block: ' +str(prev_block))
#        print('in make block leng: ' +str(type(leng)))
        out={'version':custom.version,
             'txs':txs,
             'length':leng,
             'time':time.time(),
             'target':blockchain.target(DB),
             'prevHash':tools.det_hash(prev_block)}
        out=tools.unpackage(tools.package(out))
        return out
    def POW(block, hashes, target):
        block[u'nonce']=random.randint(0,100000000000000000)
        count=0
        while tools.det_hash(block)>target and count<hashes:#this computation a little more complex than necessary. This makes it more difficult to mine bigger blocks than smaller blocks. Maybe hash(block) should= hash({'nonce':5,'else':hash(everything else))
            count+=1
            block[u'nonce']+=1
            ''' for testing sudden loss in hashpower from miners.
            if block[u'length']>150:# and block[u'nonce']%10==0:
                time.sleep(0.1)
            else:
                time.sleep(0.01)
            '''
        return block
        #try to mine a block that many times. add it to the database if we find one.
    length=stackDB.current_length()
    if length==-1:
        print('making a genesis block')
        block=genesis(reward_address, DB)
        txs=[]
    else:
        prev_block=blockchain.db_get(length, DB)
        txs=stackDB.current_txs()
        block=make_block(prev_block, txs, reward_address, DB)
    block=POW(block, hashes_till_check, blockchain.target(DB, block['length']))
    stackDB.push('suggested_blocks.db', block)
    #blockchain.add_block(block)

def peers_check(peers, DB):
    #peer=[host, port] ex. ['localhost', 8900]
    def fork_check(newblocks, DB):
        #looks at some blocks obtained from a peer. If we are on a different fork than the partner, this returns True. If we are on the same fork as the peer, then this returns False.
        try:
            length=stackDB.current_length()
            block=blockchain.db_get(length, DB)
            recent_hash=tools.det_hash(block)
            print('newblocks: ' +str(newblocks))
            return tools.det_hash(sorted(newblocks, key=lambda x: x['length'])[-1])!=recent_hash
        except:
            return False
    def peer_check(peer, DB):
        cmd=(lambda x: networking.send_command(peer, x))
        block_count=cmd({'type':'blockCount'})
        if type(block_count)!=type({'a':1}):
            return 
        if 'error' in block_count.keys():
            return         
        length=stackDB.current_length()
        ahead=int(block_count['length'])-length
        if ahead < 0:#if we are ahead of them
            print('length: ' +str(int(block_count['length'])+1))
            cmd({'type':'pushblock', 'block':blockchain.db_get(block_count['length']+1, DB)})
            return []
        if ahead == 0:#if we are on the same block, ask for any new txs
            print('ON SAME BLOCK')
            block=blockchain.db_get(length, DB)
            if 'recent_hash' in block_count and tools.det_hash(block)!=block_count['recent_hash']:
                blockchain.delete_block()
                print('WE WERE ON A FORK. time to back up.')
                return []
            my_txs=stackDB.current_txs()
            txs=cmd({'type':'txs'})
            for tx in txs:
                stackDB.push('suggested_txs.db', tx)
                #blockchain.add_tx(tx)
            pushers=[x for x in my_txs if x not in txs]
            for push in pushers:
                cmd({'type':'pushtx', 'tx':tx})
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
        times=3
        print('BEFORE FORK CHECK')
        while fork_check(blocks, DB) and times>0:
            print("IN FORK CHECK")
            times-=1
            blockchain.delete_block(DB)
        for block in blocks:
            print('hopefully blocks are coming in order')
            stackDB.push('suggested_blocks.db', block)
            #blockchain.add_block(block)
    print('peer_check: '+str(peers))
    for peer in peers:
        print('peer: ' +str(peer))
        peer_check(peer, DB)
def suggestions(DB):
    def file_map(func, file):
        things=stackDB.load(file)
        stackDB.reset(file)
        [func(x, DB) for x in things]
    map(file_map, [blockchain.add_tx, blockchain.add_block], ['suggested_txs.db', 'suggested_blocks.db'])
def mainloop(reward_address, peers, hashes_till_check, DB):
    while True:
#    for i in range(5):coun
        print('CONSENSUS')
        mine(hashes_till_check, reward_address, DB) 
        peers_check(peers, DB)
        suggestions(DB)

#mainloop('zack', [], 100000000)

