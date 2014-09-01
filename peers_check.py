"""We regularly check on peers to see if they have mined new blocks.
This file explains how we initiate interactions with our peers.
"""
import time, networking, tools, blockchain, custom, random, sys
def cmd(peer, x):
    return networking.send_command(peer, x)
def fork_check(newblocks, DB):
    block = tools.db_get(DB['length'], DB)
    recent_hash = tools.det_hash(block)
    their_hashes = map(tools.det_hash, newblocks)
    return recent_hash not in their_hashes
'''
def bounds(length, peers_block_count):
    if peers_block_count['length'] - length > custom.download_many:
        end = length + custom.download_many - 1
    else:
        end = peers_block_count['length']
    return [max(length - 2, 0), end]
'''
def bounds(length, peers_block_count):
    if peers_block_count - length > custom.download_many:
        end = length + custom.download_many - 1
    else:
        end = peers_block_count
    return [max(length - 2, 0), end]
def download_blocks(peer, DB, peers_block_count, length):
    blocks = cmd(peer, {'type': 'rangeRequest',
                        'range': bounds(length, peers_block_count['length'])})
    if not isinstance(blocks, list):
        return []
    for i in range(2):  # Only delete a max of 2 blocks, otherwise a
        # peer might trick us into deleting everything over and over.
        if fork_check(blocks, DB):
            blockchain.delete_block(DB)
    for block in blocks:
        DB['suggested_blocks'].put([block, peer])
    return 0
def ask_for_txs(peer, DB):
    txs = cmd(peer, {'type': 'txs'})
    if not isinstance(txs, list):
        return []
    for tx in txs:
        DB['suggested_txs'].put(tx)
    pushers = [x for x in DB['txs'] if x not in txs]
    for push in pushers:
        cmd(peer, {'type': 'pushtx', 'tx': push})
    return 0
def give_block(peer, DB, block_count_peer):
    #cmd(peer, {'type': 'pushblock',
    #           'block': tools.db_get(block_count_l + 1,
    #                                 DB)})
    blocks=[]
    b=bounds(block_count_peer+1, DB['length'])
    for i in range(b[0], b[1]):
        blocks.append(tools.db_get(i, DB))
    tools.log('pushing blocks: ' +str(blocks))
    cmd(peer, {'type': 'pushblock',
               'blocks': blocks})
    return 0
def peer_check(peer, DB):
    block_count = cmd(peer, {'type': 'blockCount'})
    if not isinstance(block_count, dict):
        return
    if 'error' in block_count.keys():
        return
    length = DB['length']
    size = max(len(DB['diffLength']), len(block_count['diffLength']))
    us = tools.buffer_(DB['diffLength'], size)
    them = tools.buffer_(block_count['diffLength'], size)
    if them < us:
        return give_block(peer, DB, block_count['length'])
    if us == them:
        return ask_for_txs(peer, DB)
    return download_blocks(peer, DB, block_count, length)
def exponential_random(weights):
    def grab(r, weights, counter=0):
        if len(weights)==0: return counter
        if r<weights[0]: return counter
        else: return grab(r-weights[0], weights[1:], counter+1)
    weights=map(lambda x: 1.0/x, weights)
    tot=sum(weights)
    r=random.random()*tot
    return grab(r, weights)
'''
def exponential_random(size, chance):
    while True:
        for i in range(size):
            if random.random()<chance:
                return i
'''
def main(peers, DB):
    # Check on the peers to see if they know about more blocks than we do.
    DB['peers_ranked']=[]
    for peer in peers:
        DB['peers_ranked'].append([peer, 5])
    try:
        while True:
            if DB['stop']: return
            main_once(peers, DB)
    except:
        print('main peers check: ' +str(sys.exc_info()))

def main_once(peers, DB):
        DB['peers_ranked']=sorted(DB['peers_ranked'], key=lambda r: r[1])
        time.sleep(2)
        DB['heart_queue'].put('peers check')
        #i=exponential_random(len(DB['peers_ranked']), 0.4)
        i=exponential_random(map(lambda x: x[1], DB['peers_ranked']))
        t1=time.time()
        r=peer_check(DB['peers_ranked'][i][0], DB)
        t2=time.time()
        DB['peers_ranked'][i][1]*=0.8
        if r==0:
            DB['peers_ranked'][i][1]+=0.2*(t2-t1)
        else:
            DB['peers_ranked'][i][1]+=0.2*30
        DB['heart_queue'].put('peers check')
