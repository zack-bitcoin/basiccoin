import blockchain, custom, copy, tools
#This file explains how we tell if a transaction is valid or not, it explains 
#how we update the system when new transactions are added to the blockchain.
def spend_verify(tx, txs, DB): 

    def sigs_match(sigs, pubs, msg):
        for sig in sigs:
            for pub in pubs:
                try:
                    if tools.verify(msg, sig, pub):
                        sigs.remove(sig)
                        pubs.remove(pub)
                except:
                    pass
        return len(sigs)==0

    tx_copy=copy.deepcopy(tx)
    tx_copy_2=copy.deepcopy(tx)
    tx_copy.pop('signature')
    if len(tx['id'])==0: return False
    if len(tx['signature'])>len(tx['id']): return False
    msg=tools.det_hash(tx_copy)
    if not sigs_match(copy.deepcopy(tx['signature']), copy.deepcopy(tx['id']), msg): return False
    if tx['amount']<custom.fee: return False
    address=tools.make_address(tx_copy_2['id'], len(tx_copy_2['signature']))
    return int(blockchain.db_get(address, DB)['amount'])>=int(tx['amo
unt']) 

def mint_verify(tx, txs, DB): 
    return 0==len(filter(lambda t: t['type']=='mint', txs))
tx_check={'spend':spend_verify, 'mint':mint_verify}####
#------------------------------------------------------

def adjust(key, pubkey, amount, DB):
    acc=blockchain.db_get(pubkey, DB)
    acc[key]+=amount
    blockchain.db_put(pubkey, acc, DB)

def mint(tx, DB): 
    address=tools.make_address(tx['id'], len(tx['signature']))
    adjust('amount', address, custom.block_reward, DB)
    adjust('count', address, 1, DB)

def spend(tx, DB):
    address=tools.make_address(tx['id'], len(tx['signature']))
    adjust('amount', address, -tx['amount'], DB)
    adjust('amount', tx['to'], tx['amount']-custom.fee, DB)
    adjust('count', address, 1, DB)
add_block={'mint':mint, 'spend':spend}####
#-----------------------------------------

def unmint(tx, DB):
    address=tools.make_address(tx['id'], len(tx['signature']))
    adjust('amount', address, -custom.block_reward, DB)
    adjust('count', address, -1, DB)
    
def unspend(tx, DB):
    address=tools.make_address(tx['id'], len(tx['signature']))
    adjust('amount', address, tx['amount'], DB)
    adjust('amount', tx['to'], custom.fee-tx['amount'], DB)
    adjust('count', address, -1, DB)
delete_block={'mint':unmint, 'spend':unspend}####
#------------------------------------------------
