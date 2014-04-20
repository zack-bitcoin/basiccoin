import blockchain, custom, tools, networking, stackDB, random
def mine(hashes_till_check, reward_address):
    def make_mint(pubkey): return {'type':'mint', 'id':pubkey, 'count':blockchain.count(pubkey)}
    def genesis(pubkey):
        out={'version':custom.version,
             'length':0,
             'txs':[make_mint(pubkey)]}
        out=tools.unpackage(tools.package(out))
        return out
    def make_block(prev_block, txs, pubkey):
        txs.append(make_mint(pubkey))
        out={'version':custom.version,
             'txs':txs,
             'length':prev_block['length']+1,
             'prevHash':tools.det_hash(prev_block)}
        out=tools.unpackage(tools.package(out))
        return out
    def POW(block, hashes, target):
        block[u'nonce']=random.randint(0,100000000000000000)
        while tools.det_hash(block)>target:
            block[u'nonce']+=1
        return block
        #try to mine a block that many times. add it to the database if we find one.
    length=stackDB.current_length()
    if length==-1:
        print('making a genesis block')
        block=genesis(reward_address)
        txs=[]
    else:
        prev_block=blockchain.db_get(length)
        txs=stackDB.current_txs()
        block=make_block(prev_block, txs, reward_address)
    block=POW(block, hashes_till_check, blockchain.target)
    blockchain.add_block(block)

def peers_check(peers):
    #peer=[host, port] ex. ['localhost', 8900]
    def fork_check(newblocks):
        #looks at some blocks obtained from a peer. If we are on a different fork than the partner, this returns True. If we are on the same fork as the peer, then this returns False.
        length=current_length()
        block=db_get(length)
        recent_hash=tools.det_hash(block)
        return tools.det_hash(sorted(newblocks, key=lambda x: x['length'])[-1])==recent_hash
    def peer_check(peer):
        cmd=(lambda x: networking.send_command(peer, x))
        block_count=cmd({'type':'blockCount'})
        if type(block_count)!=type({'a':1}):
            return 
        if 'error' in block_count.keys():
            return         
        length=current_length()
        ahead=int(block_count['length'])-length
        if ahead < 0:#if we are ahead of them
            print('len chain: ' +str(len(chain)))
            print('length: ' +str(int(block_count['length'])+1))
            try:
                cmd({'type':'pushblock', 'block':block})
                pushblock(db_get(str(block_count['length']+1)), peer)
            except:
                pass
            return []
        if ahead == 0:#if we are on the same block, ask for any new txs
            print('ON SAME BLOCK')
            block=db_get(length)
            if tools.det_hash(block)!=block_count['recent_hash']:
                delete_block()
                print('WE WERE ON A FORK. time to back up.')
                return []
            my_txs=load_txs()
            txs=cmd({'type':'transactions'})
            add_txs(txs)
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
        while fork_check(blocks) and times>0:
            times-=1
            delete_block()
        for block in blocks:
            print('hopefully blocks are coming in order')
            blockchain.add_block(block)
def suggestions():
    def file_map(func, file):
        things=stackDB.load(file)
        stackDB.reset(file)
        [func(x) for x in things]
    map(file_map, [blockchain.add_tx, blockchain.add_block], ['suggested_txs.db', 'suggested_blocks.db'])
def mainloop(reward_address, peers, hashes_till_check):
    while True:
#    for i in range(5):
        peers_check(peers)
        mine(hashes_till_check, reward_address)               
        suggestions()

#mainloop('zack', [], 100000000)

