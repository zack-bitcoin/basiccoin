"""This file explains how we tell if a transaction is valid or not, it explains
how we update the system when new transactions are added to the blockchain."""
import blockchain
import custom
import copy
import tools


def addr(tx):
    return tools.make_address(tx['pubkeys'], len(tx['signatures']))


def spend_verify(tx, txs, DB):

    def sigs_match(sigs, pubs, msg):
        return all(tools.verify(msg, sig, pub) for sig in sigs for pub in pubs)

    tx_copy = copy.deepcopy(tx)
    tx_copy_2 = copy.deepcopy(tx)
    tx_copy.pop('signatures')
    if len(tx['pubkeys']) == 0:
        return False
    if len(tx['signatures']) > len(tx['pubkeys']):
        return False
    msg = tools.det_hash(tx_copy)
    if not sigs_match(copy.deepcopy(tx['signatures']),
                      copy.deepcopy(tx['pubkeys']), msg):
        return False
    if tx['amount'] < custom.fee:
        return False
    address = addr(tx_copy_2)
    total_cost = 0
    for Tx in filter(lambda t: address == addr(t), [tx] + txs):
        if Tx['type'] == 'spend':
            total_cost += Tx['amount']
        if Tx['type'] == 'mint':
            total_cost -= custom.block_reward
    return int(blockchain.db_get(address, DB)['amount']) >= total_cost


def mint_verify(tx, txs, DB):
    return 0 == len(filter(lambda t: t['type'] == 'mint', txs))
tx_check = {'spend': spend_verify, 'mint': mint_verify}
#------------------------------------------------------
#DB['add_block']=True -> adding a block.

def adjust(key, pubkey, amount, DB, sign=1):
    acc = blockchain.db_get(pubkey, DB)
    if not DB['add_block']: sign=-1
    acc[key] += amount*sign
    blockchain.db_put(pubkey, acc, DB)


def mint(tx, DB):
    address = addr(tx)
    adjust('amount', address, custom.block_reward, DB)
    adjust('count', address, 1, DB)


def spend(tx, DB):
    address = addr(tx)
    adjust('amount', address, -tx['amount'], DB)
    adjust('amount', tx['to'], tx['amount'] - custom.fee, DB)
    adjust('count', address, 1, DB)
update = {'mint': mint, 'spend': spend}
#-----------------------------------------
