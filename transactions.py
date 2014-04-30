import blockchain, custom, copy, tools
import pybitcointools as pt
#This file explains how we tell if a transaction is valid or not, it explains how we update the system when new transactions are added to the blockchain.

def spend_verify(tx, txs, DB): 
    #try:
    tx_copy=copy.copy(tx)
    tx_copy.pop('signature')
    if not pt.ecdsa_verify(tools.det_hash(tx_copy), tx['signature'], tx['id']): 
        print('Qwerty')
        return False
    if tx['amount']<=custom.fee: 
        print('fksdhfshdfs')
        return False
    return blockchain.db_get(tx['id'], DB)['amount']>tx['amount']+custom.fee
    '''nn
    except:
        print('ase')
        return False
    '''
def mint_verify(tx, txs, DB):
    for t in txs:
        if t['type']=='mint': return False
    return True
tx_check={'spend':spend_verify, 'mint':mint_verify}


def adjust_amount(pubkey, amount, DB):
    try:
        acc=blockchain.db_get(pubkey, DB)
    except:
        blockchain.db_put(pubkey, {'amount': amount}, DB)
        return
    if 'amount' not in acc:
        acc['amount']=amount
    else:
        acc['amount']+=amount
    blockchain.db_put(pubkey, acc, DB)        
def adjust_count(pubkey, DB, upward=True):
    try:
        acc=blockchain.db_get(pubkey, DB)
    except:
        blockchain.db_put(pubkey, {'count': 1}, DB)
        return
    if 'count' not in acc:
        acc['count']=0
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
