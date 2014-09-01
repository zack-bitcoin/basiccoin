import blockchain, custom, math, tools
addr=tools.addr
def cost_0(txs, DB):
    #cost of the zeroth confirmation transactions
    total_cost = []
    for Tx in filter(lambda t: DB['address'] == addr(t), txs):
        def spend_(total_cost=total_cost):
            total_cost.append(custom.fee)
            total_cost += Tx['amount']
        Do={'spend':spend_,
            'mint':(lambda: total_cost.append(-custom.block_reward))}
        Do[Tx['type']]()
    return(sum(total_cost))
def fee_check(tx, txs, DB):
    address = addr(tx)
    truthcoin_cost = cost_0(txs, DB)
    acc=tools.db_get(address, DB)
    if int(acc['amount']) < truthcoin_cost: 
        tools.log('insufficient truthcoin')
        return False
    return True
def get_(loc, thing): 
    if loc==[]: return thing
    return get_(loc[1:], thing[loc[0]])
def set_(loc, dic, val):
    get_(loc[:-1], dic)[loc[-1]] = val
    return dic
def adjust(location, pubkey, DB, f):#location shouldn't be here.
    acc = tools.db_get(pubkey, DB)
    f(acc)
    tools.db_put(pubkey, acc, DB)    
def adjust_int(key, pubkey, amount, DB):
    def f(acc, amount=amount):
        if not DB['add_block']: amount=-amount
        set_(key, acc, (get_(key, acc) + amount))
    adjust(key, pubkey, DB, f)
def adjust_string(location, pubkey, old, new, DB):
    def f(acc, old=old, new=new):
        current=get_(location, acc)
        if DB['add_block']: 
            set_(location, acc, new)
        else: set_(location, acc, old)
    adjust(location, pubkey, DB, f)
def adjust_dict(location, pubkey, remove, dic, DB):
    def f(acc, remove=remove, dic=dic):
        current=get_(location, acc)
        if remove != (DB['add_block']):# 'xor' and '!=' are the same.
            current=dict(dic.items() + current.items())
        else: 
            current.pop(dic.keys()[0])
        set_(location, acc, current)
    adjust(location, pubkey, DB, f)    
def adjust_list(location, pubkey, remove, item, DB):
    def f(acc, remove=remove, item=item):
        current=get_(location, acc)
        if remove != (DB['add_block']):# 'xor' and '!=' are the same.
            current.append(item)
        else: 
            current.remove(item)
        set_(location, acc, current)
    adjust(location, pubkey, DB, f)    
def symmetric_put(id_, dic, DB):
    if DB['add_block']: tools.db_put(id_, dic, DB)
    else: tools.db_delete(id_, DB)
