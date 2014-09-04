"""This file explains how we tell if a transaction is valid or not, it explains
how we update the database when new transactions are added to the blockchain."""
import blockchain, custom, copy, tools, txs_tools
E_check=tools.E_check
def sigs_match(Sigs, Pubs, msg):
    pubs=copy.deepcopy(Pubs)
    sigs=copy.deepcopy(Sigs)
    def match(sig, pubs, msg):
        for p in pubs:
            if tools.verify(msg, sig, p):
                return {'bool':True, 'pub':pub}
        return {'bool':False}
    for sig in sigs:
        a=match(sig, pubs, msg)
        if not a['bool']:
            return False
        sigs.pop(sig)
        pubs.pop(a['pub'])
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
def spend_verify(tx, txs, DB):
    if not E_check(tx, 'to', [str, unicode]):
        tools.log('no to')
        return False
    if not signature_check(tx):
        tools.log('signature check')
        return False
    if len(tx['to'])<=30:
        tools.log('that address is too short')
        tools.log('tx: ' +str(tx))
        return False
        return False
    if not E_check(tx, 'amount', int):
        tools.log('no amount')
        return False
    tx_copy.pop('signatures')
    if not txs_tools.fee_check(tx, txs, DB):
        tools.log('fee check error')
        return False
    return True
def mint_verify(tx, txs, DB):
    return 0 == len(filter(lambda t: t['type'] == 'mint', txs))
tx_check = {'spend':spend_verify,
            'mint':mint_verify}
#------------------------------------------------------
adjust_int=txs_tools.adjust_int
adjust_dict=txs_tools.adjust_dict
adjust_list=txs_tools.adjust_list
symmetric_put=txs_tools.symmetric_put
def mint(tx, DB):
    address = tools.addr(tx)
    adjust_int(['amount'], address, custom.block_reward, DB)
    adjust_int(['count'], address, 1, DB)
def spend(tx, DB):
    address = tools.addr(tx)
    adjust_int(['amount'], address, -tx['amount'], DB)
    adjust_int(['amount'], tx['to'], tx['amount'], DB)
    adjust_int(['amount'], address, -custom.fee, DB)
    adjust_int(['count'], address, 1, DB)
update = {'mint':mint,
          'spend':spend}
