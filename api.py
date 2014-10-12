"""This is the internal API for truthshell. These are the words that are used to interact with truthcoin.
"""
import copy, tools, blockchain, custom, random, transactions, sys, time, networking, target
def sign_tx(tx_orig, DB):
    tx = copy.deepcopy(tx_orig)
    priv=db_get('privkey')
    if 'pubkeys' not in tx:
        tx['pubkeys']=[DB['pubkey']]
    try:
        tx['count'] = tools.count(DB['address'], DB)
    except:
        tx['count'] = 1
    tx['signatures'] = [tools.sign(tools.det_hash(tx), priv)]
    return tx
def easy_add_transaction(tx_orig, DB, privkey='default'):
    tx = copy.deepcopy(tx_orig)
    tx=sign_tx(tx, DB)
    if privkey in ['default', 'Default']:
        if tools.db_existence('privkey'):
            privkey=tools.db_get('privkey')
        else:
            return('no private key is known, so the tx cannot be signed. Here is the tx: \n'+str(tools.package(tx_orig).encode('base64').replace('\n', '')))
    tx['signatures'] = [tools.sign(tools.det_hash(tx), privkey)]
    return(blockchain.add_tx(tx, DB))
def help_(DB, args):      
    tell_about_command={
        'help':'type "./cli.py help <cmd>" to learn about <cmd>. type "./cli.py commands" to get a list of all truthshell commands',
        'commands':'returns a list of the truthshell commands',
        'start':'type "./cli.py start" to start truthcoin node',
        'new_address':'type "./cli.py new_address <brain>" to make a new privkey, pubkey, and address using the brain wallet=<brain>. If you want to use this address, you need to copy/paste the pubkey into the file custom.py',
        'DB_print':'prints the database that is shared between threads',
        'info':'prints the contents of an entree in the hashtable. If you want to know what the first block was: info 0, if you want to know about a particular address <addr>: info <addr>, if you want to know about yourself: info my_address',
        'my_address':'tells you your own address',
        'spend':'spends money, in satoshis, to an address <addr>. Example: spend 1000 11j9csj9802hc982c2h09ds',
        'blockcount':'returns the number of blocks since the genesis block',
        'txs':'returns a list of the zeroth confirmation transactions that are expected to be included in the next block',
        'difficulty':'returns current difficulty',
        'my_balance':'the amount of truthcoin that you own',
        'balance':'if you want to know the balance for address <addr>, type: ./cli.py balance <addr>',
        'log':'records the following words into the file "log.py"',
        'stop':'This is the correct way to stop truthcoin. If you turn off in any other way, then you are likely to corrupt your database, and you have to redownload all the blocks again.',
        'mine':'turn the miner on/off. Example to turn on: "./cli.py mine on", example to turn off: "./cli.py mine off"',
        'DB':'returns a database of information that is shared between threads',
        'pushtx':'publishes this transaction to the blockchain, will automatically sign the transaction if necessary: ./cli.py pushtx tx privkey',
        'peers':'tells you your list of peers'
    }
    if len(args)==0:
        return("needs 2 words. example: 'help help'")
    try:
        return tell_about_command[args[0]]    
    except:
        return(str(args[0])+' is not yet documented')
def peers(DB, args):
    return(str(tools.db_get('peers_ranked')))
def DB_print(DB, args):
    return(str(DB))
def info(DB, args): 
    if len(args)<1:
        return ('not enough inputs')
    if args[0]=='my_address':
        address=tools.db_get('address')
    else:
        address=args[0]
    return(str(tools.db_get(address, DB)))   
def my_address(DB, args):
    return(str(tools.db_get('address')))
def spend(DB, args): 
    if len(args)<2:
        return('not enough inputs')
    return easy_add_transaction({'type': 'spend', 'amount': int(args[0]), 'to':args[1]}, DB)
def accumulate_words(l, out=''):
    if len(l)>0: return accumulate_words(l[1:], out+' '+l[0])
    return out
def pushtx(DB, args):
    tx=tools.unpackage(args[0].decode('base64'))
    if len(args)==1:
        return easy_add_transaction(tx, DB)
    privkey=tools.det_hash(args[1])
    return easy_add_transaction(tx, DB, privkey)
def blockcount(DB, args): return(str(tools.db_get('length')))
def txs(DB, args):        return(str(tools.db_get('txs')))
def difficulty(DB, args): return(str(target.target(DB)))
def my_balance(DB, args, address='default'): 
    if address=='default':
        address=tools.db_get('address')
    return(str(tools.db_get(address, DB)['amount']-transactions.cost_0(tools.db_get('txs'), DB)['truthcoin_cost']))
def balance(DB, args): 
    if len(args)<1:
        return('what address do you want the balance for?')
    return(str(my_balance(DB, args, args[0])))
def log(DB, args): tools.log(accumulate_words(args)[1:])
def stop_(DB, args): 
    tools.db_put('stop', True)
    return('turning off all threads')
def commands(DB, args): return str(sorted(Do.keys()+['start', 'new_address', 'make_PM', 'buy_shares']))
def mine(DB, args):
    if len(args)>0 and args[0]=='off': 
        tools.db_put('mine', False)
        return('miner is now turned off')
    elif tools.db_existence('privkey'):
        tools.db_put('mine', True)
        return ('miner on. (use "./cli.py mine off" to turn off)')
    else:
        return('there is no private key with which to sign blocks. If you want to mine, you need to uncomment the "brain_wallet" line in custom.py')
def default_block(n, txs=[]):
    return({'length':int(n), 'txs':txs, 'sig_length':sig_length, 'version':custom.version, 'rand_nonce':''})
def buy_block(DB):
    length=tools.db_get('length')
    prev_block=tools.db_get(length)
    block=default_block(length+1, tools.db_get('txs'))
    if length>=0:
        to_hash=prev_block['rand_nonce']+tools.package(block['txs'])
    else:
        to_hash=prev_block['txs']
    block['rand_nonce']=tools.det_hash(to_hash)
    block=sign_tx(block, DB)
    block = tools.unpackage(tools.package(block))
    DB['suggested_blocks'].put(block)
    return block
def pass_(DB, args): return ' '
def error_(DB, args): return error
Do={'SVD_consensus':SVD_consensus, 'reveal_vote':reveal_vote, 'vote_on_decision':vote_on_decision, 'ask_decision':ask_decision, 'create_jury':create_jury, 'spend':spend, 'votecoin_spend':votecoin_spend, 'collect_winnings':collect_winnings, 'help':help_, 'blockcount':blockcount, 'txs':txs, 'balance':balance, 'my_balance':my_balance, 'b':my_balance, 'difficulty':difficulty, 'info':info, '':pass_, 'DB':DB_print, 'my_address':my_address, 'log':log, 'stop':stop_, 'commands':commands, 'pushtx':pushtx, 'mine':mine, 'peers':peers, 'buy_block':buy_block}
def main(DB, heart_queue):
    def responder(dic):
        command=dic['command']
        if command[0] in Do: 
            args=command[1:]
            try:
                out=Do[command[0]](DB, args)
            except:
                out='truthcoin api main failure : ' +str(sys.exc_info())
        else: 
            out=str(command[0]) + ' is not a command. use "./cli.py commands" to get the list of truthshell commands. use "./cli.py help help" to learn about the help tool.'
        return out
    try:
        return networking.serve_forever(responder, custom.api_port, heart_queue)
    except:
        print('api error: ' +str(sys.exc_info()))
