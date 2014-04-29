import blockchain, custom
import pybitcointools as pt


def spend_verify(tx, txs): 
    try:
        if not pt.ecdsa_verify(tools.det_hash(tx, keys), tx['signature'], db_get(tx['id'])['pubkey']): 
            print('Qwerty')
            return False
        return blockchain.db_get(tx['id'])['amount']>tx['amount']+custom.fee
    except:
        print('ase')
        return False
def mint_verify(tx, txs):
    for t in txs:
        if t['type']=='mint': return False
    return True
tx_check={'spend':spend_verify, 'mint':mint_verify}


def adjust_amount(pubkey, amount, DB):
    acc=blockchain.db_get(pubkey, DB)
    acc['amount']+=amount
    blockchain.db_put(pubkey, acc, DB)        
def adjust_count(pubkey, DB, upward=True):
    acc=blockchain.db_get(pubkey, DB)
    if upward:
        acc['count']+=1
    else:
        acc['count']-=1
    blockchain.db_put(pubkey, acc, DB)
def mint(tx, DB):
    adjust_amount(tx['id'], custom.block_reward, DB)
    adjust_count(tx['id'], DB)
def spend(tx, DB):
    adjust_amount(tx['id'], -tx['amount'], DB)
    adjust_amount(tx['to'], tx['amount']-custom.fee, DB)
    adjust_count(tx['id'], DB)
update={'mint':mint, 'spend':spend}


def unmint(tx, DB):
    adjust_amount(tx['id'], -custom.block_reward, DB)
    adjust_count(tx['id'], DB, False)
def unspend(tx, DB):
    adjust_amount(tx['id'], tx['amount'], DB)
    adjust_amount(tx['to'], -tx['amount'], DB)
    adjust_count(tx['id'], DB, False)
downdate={'mint':unmint, 'spend':unspend}
