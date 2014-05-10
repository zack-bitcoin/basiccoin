def mine(hashes_till_check, reward_address, DB):
    #tries to mine the next block hashes_till_check many times.
    def make_mint(pubkey, DB): return {'type':'mint', 'id':pubkey, 
                                       'count':blockchain.count(pubkey, DB)}
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

cmd=(lambda x: networking.send_command(peer, x))
cmd({'type':'pushblock', 
     'block':blockchain.db_get(block_count['length']+1, DB)})

#keep refreshing our idea of the current block
#
