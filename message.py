import pybitcointools as pt
import copy, state_library
#newgame_sig_list=['id', 'type', 'game_name', 'pubkey_white', 'pubkey_black', 'count', 'white', 'time', 'black', 'size', 'amount']
#nextturn_sig_list=['id', 'game_name', 'type', 'count', 'where', 'move_number']
spend_list=['id', 'amount', 'count', 'to']
message_list=['id', 'count', 'board', 'message']
message_fee=1000
block_reward=100000
def enough_funds(state, pubkey, enough):
    #if an error comes up, it would crash the miner. We need to catch all errors, and handle them intelligently. That is why I usually take 3 steps when I accept numbers from external source. I make sure the number was actually provided. I made sure the number is the type I expect. I make sure it is in the range that I expect.
    if enough==0:
        return True
    if pubkey not in state:
        print('nonexistant people have no money')
        return False
    if 'amount' not in state[pubkey]:
        print('this person has no money')
        return False
    funds=state[pubkey]['amount']
    return funds>=enough
def verify_count(tx, state):
    #What if I took a valid transaction that you signed, and tried to submit it to the blockchain repeatedly? I could steal all your money. That is why this check exists. Each transaction has a number written on it. This number increments by one every time.
    if 'id' not in tx:
        print('bad input error in verify count')
        error('here')
        return False
    if tx['id'] not in state.keys():
        state[tx['id']]={'count':1}
    if 'count' not in tx:
        print("invalid because we need each tx to have a count")
        return False
    if 'count' not in state[tx['id']]:
        state[tx['id']]['count']=1
    if 'count' in tx and tx['count']!=state[tx['id']]['count']:
        return False
    return True
def attempt_absorb(tx, state):
    #what is the resultant state after we accept this transaction?
    state=copy.deepcopy(state)
    state_orig=copy.deepcopy(state)
    if not verify_count(tx, state):
       print("invalid because the tx['count'] was wrong")
       return (state, False)
    if 'id' not in tx or type(tx['id'])  not in [type('string'), type(u'unicode')] or len(tx['id'])!=130:
        print('id error')
        return False
    state[tx['id']]['count']+=1
    types=['spend', 'mint', 'message']
    if tx['type'] not in types: 
        print('tx: ' +str(tx))
        print("invalid because tx['type'] was wrong")
        return (state_orig, False)
    if tx['type']=='mint':
        if not mint_check(tx, state):
            print('MINT ERROR')
            return (state_orig, False)
        if 'amount' not in state[tx['id']].keys():
            state[tx['id']]['amount']=0
        state[tx['id']]['amount']+=tx['amount']
    if tx['type']=='spend':
        if not spend_check(tx, state):
            print('SPEND ERROR')
            return (state_orig, False)
        if tx['to'] not in state:
            print('PUBKEY ERROR')
            state[tx['to']]={'amount':0}
        if 'amount' not in state[tx['to']]:
            state[tx['to']]['amount']=0
        state[tx['id']]['amount']-=tx['amount']
        state[tx['to']]['amount']+=tx['amount']
    if tx['type']=='message':
        if not messageCheck(tx, state):
            print('FAILED message CHECK')
            return (state_orig, False)
        if tx['board'] not in state:
            state[tx['board']]=[tx['message']]
        else:
            state[tx['board']].append(tx['message'])
        state[tx['id']]['amount']-=message_fee#1% of block reward
    return (state, True)
def mint_check(tx, state):
    if tx['amount']>10**5:
        return False#you can only mint up to 10**5 coins per block
    return True
def spend_check(tx, state):
    if tx['id'] not in state.keys():
        print("you can't spend money from a non-existant account")
        return False
    if 'amount' not in tx:
        print('how much did you want to spend?')
        return False
    if type(tx['amount']) != type(5):
        print('you can only spend integer amounts of money')
        return False
    if tx['amount']<=message_fee:
        print('the minimum amount to spend is '+str(message_fee)+' base units = 0.01 CryptGo coin.')
        return False
    if not enough_funds(state, tx['id'], tx['amount']):
        print('not enough money to spend in this account')
        return False
    if 'signature' not in tx:
        print("spend transactions must be signed")
        return False
        #    try:
    if not pt.ecdsa_verify(message2signObject(tx, spend_list), tx['signature'], tx['id'] ):
        print("bad signature")
        return False
    return True
def message2signObject(tx, keys):
    out=''
    for key in sorted(keys):
        if type(tx[key])==type([1,2]):
            string=str(key)+':'
            for i in tx[key]:
                string+=str(i)+','
        else:
            string=str(key)+':'+str(tx[key])+','
        out+=string
    return out
def messageCheck(tx, state):
    if 'board' not in tx or type(tx['board'])  not in [type('string'), type(u'unicode')] or len(tx['board'])>40:
        print('board error')
        return False
    if 'message' not in tx or type(tx['message'])  not in [type('string'), type(u'unicode')] or len(tx['message'])>140:
        print('message error')
        return False
    if not enough_funds(state, tx['id'], message_fee):
        print('not enough money')
        return False
    return True
