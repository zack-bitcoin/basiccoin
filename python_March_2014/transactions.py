"""This file explains how we tell if a transaction is valid or not, it explains
how we update the database when new transactions are added to the blockchain."""
import blockchain, custom, copy, tools
E_check=tools.E_check
def sigs_match(Sigs, Pubs, msg):
    pubs=copy.deepcopy(Pubs)
    sigs=copy.deepcopy(Sigs)
    def match(sig, pubs, msg):
        for p in pubs:
            if tools.verify(msg, sig, p):
                return {'bool':True, 'pub':p}
        return {'bool':False}
    for sig in sigs:
        a=match(sig, pubs, msg)
        if not a['bool']:
            return False
        sigs.remove(sig)
        pubs.remove(a['pub'])
    return True
def signature_check(tx):
    tx_copy = copy.deepcopy(tx)
    if not E_check(tx, 'signatures', list):
        tools.log('no signautres')
        return False
    if not E_check(tx, 'pubkeys', list):
        tools.log('no pubkeys')
        return False
    tx_copy.pop('signatures')
    if len(tx['pubkeys']) == 0:
        tools.log('pubkey error')
        return False
    if len(tx['signatures']) > len(tx['pubkeys']):
        tools.log('sigs too long')
        return False
    msg = tools.det_hash(tx_copy)
    if not sigs_match(copy.deepcopy(tx['signatures']),
                      copy.deepcopy(tx['pubkeys']), msg):
        tools.log('sigs do not match')
        return False
    return True

def spend_verify(tx, txs, out, DB):
    if not E_check(tx, 'to', [str, unicode]):
        out[0]+='no to'
        return False
    if not signature_check(tx):
        out[0]+='signature check'
        return False
    if len(tx['to'])<=30:
        out[0]+='that address is too short'
        out[0]+='tx: ' +str(tx)
        return False
    if not E_check(tx, 'amount', int):
        out[0]+='no amount'
        return False
    if not tools.fee_check(tx, txs, DB):
        out[0]+='fee check error'
        return False
    if 'vote_id' in tx:
        if not tx['to'][:-29]=='11':
            out[0]+='cannot hold votecoins in a multisig address'
            return False
    return True
def mint_verify(tx, txs, out, DB):
    return 0 == len(filter(lambda t: t['type'] == 'mint', txs))
tx_check = {'spend':spend_verify,
            'mint':mint_verify}
#------------------------------------------------------
adjust_int=tools.adjust_int
adjust_dict=tools.adjust_dict
adjust_list=tools.adjust_list
symmetric_put=tools.symmetric_put
def mint(tx, DB, add_block):
    address = tools.addr(tx)
    adjust_int(['amount'], address, custom.block_reward, DB, add_block)
    adjust_int(['count'], address, 1, DB, add_block)
def spend(tx, DB, add_block):
    address = tools.addr(tx)
    adjust_int(['amount'], address, -tx['amount'], DB, add_block)
    adjust_int(['amount'], tx['to'], tx['amount'], DB, add_block)
    adjust_int(['amount'], address, -custom.fee, DB, add_block)
    adjust_int(['count'], address, 1, DB, add_block)
update = {'mint':mint,
          'spend':spend}
