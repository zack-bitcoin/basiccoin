import blockchain, custom, copy, tools, pt
#This file explains how we tell if a transaction is valid or not, it explains 
#how we update the system when new transactions are added to the blockchain.
def spend_verify(tx, txs, DB): 
    tx_copy=copy.copy(tx)
    tx_copy.pop('signature')
    msg=tools.det_hash(tx_copy)
    if not pt.ecdsa_verify(msg, tx['signature'], tx['id']): return False
    if tx['amount']<custom.fee: return False
    if int(blockchain.db_get(tx['id'], DB)['amount'])<int(tx['amount']): 
        return False
    return True

def mint_verify(tx, txs, DB): 
    return 0==len(filter(lambda t: t['type']=='mint', txs))
tx_check={'spend':spend_verify, 'mint':mint_verify}####
#------------------------------------------------------

def adjust(key, pubkey, amount, DB):
    acc=blockchain.db_get(pubkey, DB)
    acc[key]+=amount
    blockchain.db_put(pubkey, acc, DB)

def mint(tx, DB): 
    adjust('amount', tx['id'], custom.block_reward, DB)
    adjust('count', tx['id'], 1, DB)

def spend(tx, DB):
    adjust('amount', tx['id'], -tx['amount'], DB)
    adjust('amount', tx['to'], tx['amount']-custom.fee, DB)
    adjust('count', tx['id'], 1, DB)
add_block={'mint':mint, 'spend':spend}####
#-----------------------------------------

def unmint(tx, DB):
    adjust('amount', tx['id'], -custom.block_reward, DB)
    adjust('count', tx['id'], -1, DB)
    
def unspend(tx, DB):
    adjust('amount', tx['id'], tx['amount'], DB)
    adjust('amount', tx['to'], custom.fee-tx['amount'], DB)
    adjust('count', tx['id'], -1, DB)
delete_block={'mint':unmint, 'spend':unspend}####
#------------------------------------------------
