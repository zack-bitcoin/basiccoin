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
import sys
def make_mint(pubkey, DB):
    address = tools.make_address([pubkey], 1)
    return {'type': 'mint',
            'pubkeys': [pubkey],
            'signatures': ['first_sig'],
            'count': tools.count(address, DB)}
def genesis(pubkey, DB):
    target = blockchain.target(DB)
    out = {'version': custom.version,
           'length': 0,
           'time': time.time(),
           'target': target,
           'diffLength': blockchain.hexInvert(target),
           'txs': [make_mint(pubkey, DB)]}
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
def POW(block, restart_signal):
    halfHash = tools.det_hash(block)
    block[u'nonce'] = random.randint(0, 10000000000000000000000000000000000000000)
    count = 0
    while tools.det_hash({u'nonce': block['nonce'],
                          u'halfHash': halfHash}) > block['target']:
        count += 1
        block[u'nonce'] += 1
        if restart_signal.is_set():
            restart_signal.clear()
            return {'solution_found': True}
    return block
def new_worker(solution_queue):
    in_queue=multiprocessing.Queue()
    restart=multiprocessing.Event()
    proc = multiprocessing.Process(target=miner, args=(restart, solution_queue, in_queue))
    proc.daemon=True
    proc.start()
    return({'in_queue':in_queue, 'restart':restart, 'solution_queue':solution_queue, 'proc':proc})
def dump_out(queue):
    while not queue.empty():
        try:
            queue.get(False)
        except:
            pass
def restart_workers(workers):
    for worker in workers:
        dump_out(worker['in_queue'])
        worker['restart'].set()
def main(pubkey, DB):
    num_cores = multiprocessing.cpu_count()
    solution_queue = multiprocessing.Queue()
    workers = [new_worker(solution_queue) for _ in range(num_cores)]
    try:
        while True:
            time.sleep(2)
            if DB['stop']: return
            if DB['mine']:
                main_once(pubkey, DB, num_cores, solution_queue, workers)
    except:
        print('miner main: ' +str(sys.exc_info()))
def main_once(pubkey, DB, num_cores, solution_queue, workers):
    DB['heart_queue'].put('miner')
    if DB['length']==-1:
        candidate_block = genesis(pubkey, DB)
    else:
        prev_block = tools.db_get(DB['length'], DB)
        candidate_block = make_block(prev_block, DB['txs'], pubkey, DB)
    work = candidate_block
    for worker in workers:
        worker['in_queue'].put(work)
        worker['in_queue'].put(work)
    while solution_queue.empty():
        time.sleep(1)
    restart_workers(workers)
    while not solution_queue.empty():
        try:
            DB['suggested_blocks'].put(solution_queue.get(False))
        except:
            continue
def miner(restart, solution_queue, in_queue):
    while True:
        try:
            candidate_block=in_queue.get(False)
        except:
            continue
        possible_block = POW(candidate_block, restart)
        if 'error' in possible_block: 
            continue
        elif 'solution_found' in possible_block: 
            continue
        else:
            solution_queue.put(possible_block)
