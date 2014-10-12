"""This file explains how we tell if a transaction is valid or not, it explains
how we update the database when new transactions are added to the blockchain."""
import blockchain, custom, copy, tools
E_check=tools.E_check
def cost_to_buy_shares(tx, DB):
    pm=tools.db_get(tx['PM_id'], DB)
    shares_purchased=pm['shares_purchased']
    buy=tx['buy']
    B=pm['B']
    def C(shares, B): return B*math.log(sum(map(lambda x: math.e**(x/B), shares)))
    C_old=C(shares_purchased, B)
    def add(a, b): return a+b
    C_new=C(map(add, shares_purchased, buy), B)
    return int(C_new-C_old)
def cost_0(txs, DB):
    #cost of the zeroth confirmation transactions
    total_cost = []
    votecoin_cost = {}
    address=tools.db_get('address')
    for Tx in filter(lambda t: address == addr(t), txs):
        def spend_(total_cost=total_cost, votecoin_cost=votecoin_cost):
            total_cost.append(custom.fee)
            if 'vote_id' not in Tx:
                total_cost += [Tx['amount']]
            else:
                if Tx['vote_id'] not in votecoin_cost: 
                    votecoin_cost[Tx['vote_id']]=0
                votecoin_cost[Tx['vote_id']]+=Tx['amount']
        def buy_shares_(total_cost=total_cost):
            cost = cost_to_buy_shares(Tx, DB)
            total_cost.append(custom.buy_shares_fee)
            total_cost.append(cost)
            total_cost.append(int(abs(cost*0.01)))
        Do={'spend':spend_,
            'mint':(lambda: total_cost.append(-custom.block_reward)), 
            'create_jury':(lambda: total_cost.append(custom.create_jury_fee)), 
            'propose_decision':(lambda: total_cost.append(custom.propose_decision_fee)), 
            'jury_vote':(lambda: total_cost.append(custom.jury_vote_fee)),
            'reveal_jury_vote':(lambda: total_cost.append(custom.reveal_jury_vote_fee)),
            'SVD_consensus':(lambda: total_cost.append(custom.SVD_consensus_fee)),
            'collect_winnings':(lambda: total_cost.append(-custom.collect_winnings_reward)),
            'buy_shares':buy_shares_,
            'prediction_market':(lambda: total_cost.append(Tx['B']*math.log(len(Tx['states']))))}
        Do[Tx['type']]()
    return {'truthcoin_cost':sum(total_cost), 'votecoin_cost':votecoin_cost}
def fee_check(tx, txs, DB):
    address = addr(tx)
    cost_=cost_0(txs+[tx], DB)
    truthcoin_cost = cost_['truthcoin_cost']
    votecoin_cost = cost_['votecoin_cost']
    acc=tools.db_get(address, DB)
    if int(acc['amount']) < truthcoin_cost: 
        tools.log('insufficient truthcoin')
        return False
    for v_id in votecoin_cost:
        if v_id not in acc['votecoin']: 
            tools.log('votecoin_cost: ' +str(votecoin_cost))
            tools.log('acc: ' +str(acc))
            tools.log('0 votecoin: ' +str(v_id))
            return False
        if acc['votecoin'][v_id]<votecoin_cost[v_id]: 
            tools.log(acc['votecoin'][v_id])
            tools.log(votecoin_cost[v_id])
            tools.log('not enough votecoin: ' +str(v_id))
            return False
    return True
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
    if not fee_check(tx, txs, DB):
        out[0]+='fee check error'
        return False
    if 'vote_id' in tx:
        if not tx['to'][:-29]=='11':
            out[0]+='cannot hold votecoins in a multisig address'
            return False
    return True
def sign_verify(tx, txs, DB):
    #were we elected 3000 blocks ago?
    #SHA256(all the seeds in the last 100 blocks on the old chain, addr(tx))<2^256 *64*balance/(total money supply)
    address=tools.addr(tx)
    acc=tools.db_get(address, DB)
    if acc['blacklist']=='true': 
        tools.log('blocklisted address: ' +str(address))
        return False
    if not E_check(tx, 'sign_on', int):
        tools.log('no secret_hash')
        return False
    if tx['sign_on']<tools.db_get('length')-10:
        return False
    for sh in acc['secret_hashes']:
        if sh[1]==tx['sign_on']:
            #tools.log('already signed on that block')
            return False
    for t in txs:
        if t['type']==tx['type']:
            if t['sign_on']==tx['sign_on']:
                if tools.addr(t)==address:
                    #tools.log('already signed on that block, in a different zero confirmation transaction')
                    return False
    if not signature_check(tx):
        tools.log('signature check')
        return False
    if not E_check(tx, 'secret_hash', [str, unicode]):
        tools.log('no secret_hash')
        return False
    if not E_check(tx, 'rand_nonce', [str, unicode]):
        tools.log('no rand_nonce')
        return False
    block=tools.db_get(tx['sign_on'], DB)
    if tx['rand_nonce']!=block['rand_nonce']:
        tools.log('sign block_hash does not match')
        return False
    if not signer_p(address, tx['sign_on'], DB):
        tools.log('you were not elected as a signer error')
        return False
    return True
def signer_p(address, sign_on, DB):
    seeds=seed_range(sign_on-2000, sign_on-1900, DB)
    my_size=tools.det_hash(seeds+address)
    balance=blockchain.old_chain(lambda DB: tools.db_get(address, DB)['amount'], DB)
    if type(balance)!=type(1):
        return False
    target=tools.target_times_float('f'*64, 64*balance/custom.total_money)
    size=max(len(my_size), len(target))
    return tools.buffer_(my_size, size)<=tools.buffer_(target, size)
def reveal_secret_verify(tx, txs, DB):
    address=tools.addr(tx)
    acc=tools.db_get(address, DB)
    if not E_check(tx, 'sign_on', int):
        tools.log('what length did you sign')
        return False
    length=tools.db_get('length')
    if tx['sign_on']>=length-100:
        tools.log('too soon')
        return False
    if tx['sign_on']<=length-1000:
        tools.log('too late')
        return False
    if not signature_check(tx):#otherwise miners will censor his reveal.
        tools.log('signature check')
        return False
    for s in acc['secrets']:
        if s[1]==tx['sign_on']:
            tools.log('already revealed the secret stored at that length')
        if s[0]==tx['secret']:
            tools.log('already revealed that secret')
            return False
    for t in txs:
        if t['type']==tx['type']:
            if tools.addr(t)==address:
                if t['sign_on']==tx['sign_on']:
                    tools.log('already revealed that length in a different zeroth confirmation tx')
                    return False
    if not E_check(tx, 'secret_hash', [str, unicode]):
        tools.log('no secret_hash')
        return False
    if not E_check(tx, 'secret', [str, unicode]):
        tools.log('no secret')
        return False
    for sh in acc['secret_hashes']:
        if sh[1]==tx['sign_on']:
            hash_=sh[0]
    if not det_hash(tx['secret'])==hash_:
        tools.log('secret does not match secret_hash')
        return False
    return True
def slasher_double_sign_verify(tx, txs, DB):
    if not signatures_check(tx['tx1']): return False
    if not signatures_check(tx['tx2']): return False
    if tools.addr(tx['tx1'])!=tools.addr(tx['tx2']): return False
    address=tools.addr(tx['tx1'])
    acc=tools.db_get(address, DB)
    if acc['expiration']<tools.db_get('length'): return False
    for sh in acc['secret_hashes']:
        flag=True
        if sh[1]==tx['tx1']['sign_on']:
            flag=False
        if flag:
            return False
    if tx['tx1']['sign_on'] != tx['tx2']['sign_on']: return False
    if tx['tx1']['type'] != tx['tx2']['type']: return False
    if tx['tx1']['type'] != 'sign': return False
    if tx['tx1']['block_hash'] == tx['tx2']['block_hash']: return False
    return True

def slasher_early_reveal_verify(DB):
    return True

def register_verify(DB):
    return True

tx_check = {'spend':spend_verify,
            'register':register_verify,
            'sign':sign_verify,
            'reveal_secret':reveal_secret_verify,
            'slasher_early_reveal':slasher_early_reveal_verify,
            'slasher_double_sign':slasher_double_sign_verify}
#------------------------------------------------------
def get_(loc, thing): 
    if loc==[]: return thing
    return get_(loc[1:], thing[loc[0]])
def set_(loc, dic, val):
    get_(loc[:-1], dic)[loc[-1]] = val
    return dic
def adjust(pubkey, DB, f):#location shouldn't be here.
    acc = tools.db_get(pubkey, DB)
    f(acc)
    tools.db_put(pubkey, acc, DB)    
def adjust_int(key, pubkey, amount, DB, add_block):
    def f(acc, amount=amount):
        if not add_block: amount=-amount
        set_(key, acc, (get_(key, acc) + amount))
    adjust(pubkey, DB, f)
def adjust_string(location, pubkey, old, new, DB, add_block):
    def f(acc, old=old, new=new):
        current=get_(location, acc)
        if add_block: 
            set_(location, acc, new)
        else: set_(location, acc, old)
    adjust(pubkey, DB, f)
def adjust_dict(location, pubkey, remove, dic, DB, add_block):
    def f(acc, remove=remove, dic=dic):
        current=get_(location, acc)
        if remove != add_block:# 'xor' and '!=' are the same.
            current=dict(dic.items() + current.items())
        else: 
            current.pop(dic.keys()[0])
        set_(location, acc, current)
    adjust(pubkey, DB, f)    
def adjust_list(location, pubkey, remove, item, DB, add_block):
    def f(acc, remove=remove, item=item):
        current=get_(location, acc)
        if remove != (add_block):# 'xor' and '!=' are the same.
            current.append(item)
        else: 
            current.remove(item)
        set_(location, acc, current)
    adjust(pubkey, DB, f)    
def symmetric_put(id_, dic, DB, add_block):
    if add_block: tools.db_put(id_, dic, DB)
    else: tools.db_delete(id_, DB)
def spend(tx, DB, add_block):
    address = tools.addr(tx)
    adjust_int(['amount'], address, -tx['amount'], DB, add_block)
    adjust_int(['amount'], tx['to'], tx['amount'], DB, add_block)
    adjust_int(['amount'], address, -custom.fee, DB, add_block)
    adjust_int(['count'], address, 1, DB, add_block)
def sign(tx, DB):
    address = tools.addr(tx)
    adjust_int(['count'], address, 1, DB)
    adjust_list(['secret_hashes'], address, False, [tx['secret_hash'], tx['sign_on']], DB)#list to dict
    #DB['sig_length'] should get longer.
def reveal_secret(tx, DB):
    #reveals secret, pays reward
    address=tools.addr(tx)
    adjust_int('count', address, 1, DB)
    adjust_int('amount', address, custom.pos_reward, DB)
    adjust_list(['secrets'], address, False, [tx['secret'], tx['sign_on']], DB)#list to dict
    #adjust_list('secret_hashes', tx['sign_on'], True, secret(tx), DB)
    #adjust_list('secrets', tx['sign_on'], False, tx['secret'], DB)
def slasher_double_sign(tx, DB):
    t=tx['tx1']#<--this tx is on our chain
    address=tools.addr(t)
    adjust_list(['secret_hashes'], address, True, [t['secret_hash'], t['sign_on']])
def slasher_early_reveal(DB):
    pass

def register(DB):
    pass


update = {'spend':spend,
          'register':register,
          'sign':sign,
          'reveal_secret':reveal_secret,
          'slasher_early_reveal':slasher_early_reveal,
          'slasher_double_sign':slasher_double_sign}

