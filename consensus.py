""" This file mines blocks and talks to peers. It maintains consensus of the
    blockchain.
"""
from Queue import Empty

import blockchain
import copy
import custom
import tools
import networking
import multiprocessing
import random
import time
import copy


def peers_check(peers, DB):
    # Check on the peers to see if they know about more blocks than we do.
    def peer_check(peer, DB):

        def cmd(x):
            return networking.send_command(peer, x)

        def download_blocks(peer, DB, peers_block_count, length):

            def fork_check(newblocks, DB):
                block = blockchain.db_get(DB['length'], DB)
                recent_hash = tools.det_hash(block)
                their_hashes = map(tools.det_hash, newblocks)
                return recent_hash not in their_hashes

            def bounds(length, peers_block_count):
                if peers_block_count['length'] - length > custom.download_many:
                    end = length + custom.download_many - 1
                else:
                    end = peers_block_count['length']
                return [max(length - 2, 0), end]

            blocks = cmd({'type': 'rangeRequest',
                          'range': bounds(length, peers_block_count)})
            if not isinstance(blocks, list):
                return []
            for i in range(2):  # Only delete a max of 2 blocks, otherwise a
                # peer might trick us into deleting everything over and over.
                if fork_check(blocks, DB):
                    blockchain.delete_block(DB)
            DB['suggested_blocks'].extend(blocks)
            return

        def ask_for_txs(peer, DB):
            txs = cmd({'type': 'txs'})
            DB['suggested_txs'].extend(txs)
            pushers = [x for x in DB['txs'] if x not in txs]
            for push in pushers:
                cmd({'type': 'pushtx', 'tx': push})
            return []

        def give_block(peer, DB, block_count):
            cmd({'type': 'pushblock',
                 'block': blockchain.db_get(block_count['length'] + 1,
                                            DB)})
            return []

        block_count = cmd({'type': 'blockCount'})
        if not isinstance(block_count, dict):
            return
        if 'error' in block_count.keys():
            return
        length = DB['length']
        size = max(len(DB['diffLength']), len(block_count['diffLength']))
        us = tools.buffer_(DB['diffLength'], size)
        them = tools.buffer_(block_count['diffLength'], size)
        if them < us:
            return give_block(peer, DB, block_count)
        if us == them:
            return ask_for_txs(peer, DB)
        return download_blocks(peer, DB, block_count, length)

    for peer in peers:
        peer_check(peer, DB)


def suggestions(DB):
    [blockchain.add_tx(tx, DB) for tx in DB['suggested_txs']]
    DB['suggested_txs'] = []
    [blockchain.add_block(block, DB) for block in DB['suggested_blocks']]
    DB['suggested_blocks'] = []


def mainloop(peers, DB):
    while True:
        time.sleep(1)
        peers_check(peers, DB)
        suggestions(DB)


def miner_controller(reward_address, peers, hashes_till_check, DB):
    """ Spawns worker CPU mining processes and coordinates the effort."""
    def make_mint(pubkey, DB):
        address = tools.make_address([reward_address], 1)
        return {'type': 'mint',
                'pubkeys': [pubkey],
                'signatures': ['first_sig'],
                'count': blockchain.count(address, DB)}

    def genesis(pubkey, DB):
        target = blockchain.target(DB)
        out = {'version': custom.version,
               'length': 0,
               'time': time.time(),
               'target': target,
               'diffLength': blockchain.hexInvert(target),
               'txs': [make_mint(pubkey, DB)]}
        print('out: ' + str(out))
        out = tools.unpackage(tools.package(out))
        return out

    def make_block(prev_block, txs, pubkey, DB):
        leng = int(prev_block['length']) + 1
        target = blockchain.target(DB, leng)
        diffLength = blockchain.hexSum(prev_block['diffLength'],
                                       blockchain.hexInvert(target))
        out = {'version': custom.version,
               'txs': txs + [make_mint(pubkey, DB)],
               'length': leng,
               'time': time.time(),
               'diffLength': diffLength,
               'target': target,
               'prevHash': tools.det_hash(prev_block)}
        out = tools.unpackage(tools.package(out))
        return out
    def restart_workers():
        print("Possible solution found, restarting mining workers.")
        for worker_mailbox in worker_mailboxes:
            worker_mailbox['restart'].set()

    def spawn_worker():
        print("Spawning worker")
        restart_signal = multiprocessing.Event()
        work_queue = multiprocessing.Queue()
        worker_proc = multiprocessing.Process(target=miner,
                                              args=(submitted_blocks, work_queue,
                                                    restart_signal))
        worker_proc.daemon = True
        worker_proc.start()
        return {'restart': restart_signal, 'worker': worker_proc,
                'work_queue': work_queue}

    submitted_blocks = multiprocessing.Queue()
    num_cores = multiprocessing.cpu_count()
    print("Creating %d mining workers." % num_cores)
    worker_mailboxes = [spawn_worker() for _ in range(num_cores)]
    candidate_block = None
    length = None
    while True:
        length = DB['length']
        if length == -1:
            candidate_block = genesis(reward_address, DB)
            txs = []
        else:
            prev_block = blockchain.db_get(length, DB)
            txs = DB['txs']
            candidate_block = make_block(prev_block, txs, reward_address, DB)

        work = (candidate_block, hashes_till_check)

        for worker_mailbox in worker_mailboxes:
            worker_mailbox['work_queue'].put(copy.copy(work))

        # When block found, add to suggested blocks.
        solved_block = submitted_blocks.get()  # TODO(roasbeef): size=1?
        if solved_block['length'] != length + 1:
            continue
        DB['suggested_blocks'].append(solved_block)
        restart_workers()


def miner(block_submit_queue, get_work_queue, restart_signal):
    def POW(block, hashes):
        halfHash = tools.det_hash(block)
        block[u'nonce'] = random.randint(0, 10000000000000000000000000000000000000000)
        count = 0
        while tools.det_hash({u'nonce': block['nonce'],
                              u'halfHash': halfHash}) > block['target']:
            count += 1
            block[u'nonce'] += 1
            if count > hashes:
                return {'error': False}
            if restart_signal.is_set():
                restart_signal.clear()
                return {'solution_found': True}
            ''' for testing sudden loss in hashpower from miners.
            if block[u'length']>150:
            else: time.sleep(0.01)
            '''
        return block
    block_header = None
    need_new_work = False
    while True:
        # Either get the current block header, or restart because a block has
        # been solved by another worker.
        try:
            if need_new_work or block_header is None:
                block_header, hashes_till_check = get_work_queue.get(True, 1)
                need_new_work = False
        # Try to optimistically get the most up-to-date work.
        except Empty:
            need_new_work = False
            continue

        possible_block = POW(block_header, hashes_till_check)
        if 'error' in possible_block:  # We hit the hash ceiling.
            continue
        # Another worker found the block.
        elif 'solution_found' in possible_block:
            # Empty out the signal queue.
            need_new_work = True
        # We've found a block!
        else:
            block_submit_queue.put(block_header)
            need_new_work = True
