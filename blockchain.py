""" This file explains how we talk to the database. It explains the rules for
    adding blocks and transactions.
"""
import time
import copy
import custom
import tools
import networking
import transactions


def db_get(n, DB):
    n = str(n)
    try:
        return tools.unpackage(DB['db'].Get(n))
    except:
        db_put(n, {'count': 0, 'amount': 0}, DB)  # Everyone defaults with
        # having zero money, and having broadcast zero transcations.
        return db_get(n, DB)


def db_put(key, dic, DB):
    return DB['db'].Put(str(key), tools.package(dic))


def db_delete(key, DB):
    return DB['db'].Delete(str(key))


def count(address, DB):
    # Returns the number of transactions that pubkey has broadcast.

    def zeroth_confirmation_txs(address, DB):
        def is_zero_conf(t):
            return address == tools.make_address(t['pubkeys'], len(t['signatures']))
        return len(filter(is_zero_conf, DB['txs']))

    current = db_get(address, DB)['count']
    return current+zeroth_confirmation_txs(address, DB)


def add_tx(tx, DB):
    # Attempt to add a new transaction into the pool.
    address = tools.make_address(tx['pubkeys'], len(tx['signatures']))

    def verify_count(tx, txs):
        return tx['count'] != count(address, DB)

    def type_check(tx, txs):
        if 'type' not in tx:
            return True
        if tx['type'] == 'mint':
            return True
        return tx['type'] not in transactions.tx_check

    def too_big_block(tx, txs):
        return len(tools.package(txs+[tx])) > networking.MAX_MESSAGE_SIZE - 5000

    def verify_tx(tx, txs):
        if type_check(tx, txs):
            return False
        if tx in txs:
            return False
        if verify_count(tx, txs):
            return False
        if too_big_block(tx, txs):
            return False
        return transactions.tx_check[tx['type']](tx, txs, DB)

    if verify_tx(tx, DB['txs']):
        DB['txs'].append(tx)

targets = {}
times = {}  # Stores blocktimes


def recent_blockthings(key, DB, size, length=0):
    # Grabs info from old blocks.
    if key == 'time':
        storage = times
    if key == 'target':
        storage = targets

    def get_val(length):
        leng = str(length)
        if not leng in storage:
            storage[leng] = db_get(leng, DB)[key]
        return storage[leng]

    if length == 0:
        length = DB['length']
    start = (length-size) if (length-size) >= 0 else 0
    return map(get_val, range(start, length))


def hexSum(a, b):
    # Sum of numbers expressed as hexidecimal strings
    return tools.buffer_(str(hex(int(a, 16)+int(b, 16)))[2: -1], 64)


def hexInvert(n):
    # Use double-size for division, to reduce information leakage.
    return tools.buffer_(str(hex(int('f' * 128, 16) / int(n, 16)))[2: -1], 64)


def target(DB, length=0):
    """ Returns the target difficulty at a paticular blocklength. """
    if length == 0:
        length = DB['length']
    if length < 4:
        return '0' * 4 + 'f' * 60  # Use same difficulty for first few blocks.
    if length <= DB['length']:
        return targets[str(length)]  # Memoized

    def targetTimesFloat(target, number):
        a = int(str(target), 16)
        b = int(a * number)
        return tools.buffer_(str(hex(b))[2: -1], 64)

    def weights(length):
        return [custom.inflection ** (length-i) for i in range(length)]

    def estimate_target(DB):
        """
        We are actually interested in the average number of hashes required to
        mine a block. number of hashes required is inversely proportional
        to target. So we average over inverse-targets, and inverse the final
        answer. """
        def sumTargets(l):
            if len(l) < 1:
                return 0
            while len(l) > 1:
                l = [hexSum(l[0], l[1])] + l[2:]
            return l[0]

        targets = recent_blockthings('target', DB, custom.history_length)
        w = weights(len(targets))
        tw = sum(w)
        targets = map(hexInvert, targets)

        def weighted_multiply(i):
            return targetTimesFloat(targets[i], w[i]/tw)
        weighted_targets = [weighted_multiply(i) for i in range(len(targets))]
        return hexInvert(sumTargets(weighted_targets))

    def estimate_time(DB):
        times = recent_blockthings('time', DB, custom.history_length)
        blocklengths = [times[i] - times[i - 1] for i in range(1, len(times))]
        w = weights(len(blocklengths))  # Geometric weighting
        tw = sum(w)  # Normalization constant
        return sum([w[i] * blocklengths[i] / tw for i in range(len(blocklengths))])

    retarget = estimate_time(DB) / custom.blocktime(length)
    return targetTimesFloat(estimate_target(DB), retarget)


def add_block(block, DB):
    """Attempts adding a new block to the blockchain.
     Median is good for weeding out liars, so long as the liars don't have 51%
     hashpower. """
    def median(mylist):
        if len(mylist) < 1:
            return 0
        return sorted(mylist)[len(mylist) / 2]

    def block_check(block, DB):
        def tx_check(txs):
            start = copy.deepcopy(txs)
            out = []
            start_copy = []
            while start != start_copy:
                if start == []:
                    return False  # Block passes this test
                start_copy = copy.deepcopy(start)
                if transactions.tx_check[start[-1]['type']](start[-1], out, DB):
                    out.append(start.pop())
                else:
                    return True  # Block is invalid
            return True  # Block is invalid
        if not isinstance(block, dict):
            return False
        if 'error' in block:
            return False
        if 'length' not in block:
            return False
        length = DB['length']
        if int(block['length']) != int(length) + 1:
            return False
        if block['diffLength'] != hexSum(DB['diffLength'],
                                         hexInvert(block['target'])):
            return False
        if length >= 0:
            if tools.det_hash(db_get(length, DB)) != block['prevHash']:
                return False
        a = copy.deepcopy(block)
        a.pop('nonce')
        if u'target' not in block.keys():
            return False
        half_way = {u'nonce': block['nonce'], u'halfHash': tools.det_hash(a)}
        if tools.det_hash(half_way) > block['target']:
            return False
        if block['target'] != target(DB, block['length']):
            return False
        earliest = median(recent_blockthings('time', DB, custom.mmm))
        if 'time' not in block:
            return False
        if block['time'] > time.time():
            return False
        if block['time'] < earliest:
            return False
        if tx_check(block['txs']):
            return False
        return True

    if block_check(block, DB):
        print('add_block: ' + str(block))
        db_put(block['length'], block, DB)
        DB['length'] = block['length']
        DB['diffLength'] = block['diffLength']
        orphans = copy.deepcopy(DB['txs'])
        DB['txs'] = []
        for tx in block['txs']:
            DB['add_block']=True
            transactions.update[tx['type']](tx, DB)
        for tx in orphans:
            add_tx(tx, DB)


def delete_block(DB):
    """ Removes the most recent block from the blockchain. """
    if DB['length'] < 0:
        return
    try:
        targets.pop(str(DB['length']))
    except:
        pass
    try:
        times.pop(str(DB['length']))
    except:
        pass
    block = db_get(DB['length'], DB)
    orphans = copy.deepcopy(DB['txs'])
    DB['txs'] = []
    for tx in block['txs']:
        orphans.append(tx)
        DB['add_block']=False
        transactions.update[tx['type']](tx, DB)
    db_delete(DB['length'], DB)
    DB['length'] -= 1
    if DB['length'] == -1:
        DB['diffLength'] = '0'
    else:
        block = db_get(DB['length'], DB)
        DB['diffLength'] = block['diffLength']
    for orphan in sorted(orphans, key=lambda x: x['count']):
        add_tx(orphan, DB)
