"""This is the internal API. These are the words that are used to interact with a local node that you have the password to.
"""
import copy, tools, blockchain, custom, random, transactions, sys, time, networking, target
def easy_add_transaction(tx_orig, DB, privkey='default'):
    tx = copy.deepcopy(tx_orig)
    if privkey in ['default', 'Default']:
        if tools.db_existence('privkey'):
            privkey=tools.db_get('privkey')
        else:
            return('no private key is known, so the tx cannot be signed. Here is the tx: \n'+str(tools.package(tx_orig).encode('base64').replace('\n', '')))
    pubkey=tools.privtopub(privkey)
    address=tools.make_address([pubkey], 1)
    if 'count' not in tx:
        try:
            tx['count'] = tools.count(address, {})
        except:
            tx['count'] = 1
    if 'pubkeys' not in tx:
        tx['pubkeys']=[pubkey]
    if 'signatures' not in tx:
        tx['signatures'] = [tools.sign(tools.det_hash(tx), privkey)]
    return(blockchain.add_tx(tx, DB))
def help_(DB, args):      
    tell_about_command={
        'help':'type "./cli.py help <cmd>" to learn about <cmd>. type "./cli.py commands" to get a list of all commands',
        'commands':'returns a list of the commands',
        'start':'type "./cli.py start" to start a full node',
        'new_address':'type "./cli.py new_address <brain>" to make a new privkey, pubkey, and address using the brain wallet=<brain>. If you want to use this address, you need to copy/paste the pubkey into the file custom.py',
        'DB_print':'prints the database that is shared between threads',
        'info':'prints the contents of an entree in the hashtable. If you want to know what the first block was: info 0, if you want to know about a particular address <addr>: info <addr>, if you want to know about yourself: info my_address',
        'my_address':'tells you your own address',
        'spend':'spends money, in satoshis, to an address <addr>. Example: spend 1000 11j9csj9802hc982c2h09ds',
        'blockcount':'returns the number of blocks since the genesis block',
        'txs':'returns a list of the zeroth confirmation transactions that are expected to be included in the next block',
        'difficulty':'returns current difficulty',
        'my_balance':'the amount of money that you own',
        'balance':'if you want to know the balance for address <addr>, type: ./cli.py balance <addr>',
        'log':'records the following words into the file "log.py"',
        'stop':'This is the correct way to stop the node. If you turn off in any other way, then you are likely to corrupt your database, and you have to redownload all the blocks again.',
        'mine':'turn the miner on/off',
        'DB':'returns a database of information that is shared between threads',
        'pushtx':'publishes this transaction to the blockchain, will automatically sign the transaction if necessary: ./cli.py pushtx tx privkey',
        'peers':'tells you your list of peers'
    }
    if len(args)==0:
        return("needs 2 words. example: 'help help'")
    try:
        return tell_about_command[args[0]]    
    except:
        return(str(args[0])+' is not a word in the help documentation.')
def peers(DB, args):
    return(tools.db_get('peers_ranked'))
def DB_print(DB, args):
    return(DB)
def info(DB, args): 
    if len(args)<1:
        return ('not enough inputs')
    if args[0]=='my_address':
        address=tools.db_get('address')
    else:
        address=args[0]
    return(tools.db_get(address, DB))
def my_address(DB, args):
    return(tools.db_get('address'))
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
def blockcount(DB, args): return(tools.db_get('length'))
def txs(DB, args):        return(tools.db_get('txs'))
def difficulty(DB, args): return(target.target(DB))
def my_balance(DB, args, address='default'): 
    if address=='default':
        address=tools.db_get('address')
    return(tools.db_get(address, DB)['amount']-tools.cost_0(tools.db_get('txs'), address))
def balance(DB, args): 
    if len(args)<1:
        return('what address do you want the balance for?')
    return(my_balance(DB, args, args[0]))
def log(DB, args): tools.log(accumulate_words(args)[1:])
def stop_(DB, args): 
    tools.db_put('stop', True)
    return('turning off all threads')
def commands(DB, args): return sorted(Do.keys()+['start', 'new_address'])
def mine(DB, args):
    m=not(tools.db_get('mine'))
    tools.db_put('mine', m)
    if m: 
        m='on'
    else: 
        m='off'
    return('miner is currently: ' +m)
def pass_(DB, args): return ' '
def error_(DB, args): return error
Do={'spend':spend, 'help':help_, 'blockcount':blockcount, 'txs':txs, 'balance':balance, 'my_balance':my_balance, 'b':my_balance, 'difficulty':difficulty, 'info':info, '':pass_, 'DB':DB_print, 'my_address':my_address, 'log':log, 'stop':stop_, 'commands':commands, 'pushtx':pushtx, 'mine':mine, 'peers':peers}
def main(DB, heart_queue):
    def responder(dic):
        command=dic['command']
        if command[0] in Do: 
            args=command[1:]
            try:
                out=Do[command[0]](DB, args)
            except Exception as exc:
                tools.log(exc)
                out='api main failure : ' +str(sys.exc_info())
        else: 
            out=str(command[0]) + ' is not a command. use "./cli.py commands" to get the list of commands. use "./cli.py help help" to learn about the help tool.'
        return out
    try:
        return networking.serve_forever(responder, custom.api_port, heart_queue)
    except Exception as exc:
        tools.log('api error')
        tools.log(exc)
