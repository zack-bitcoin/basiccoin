"""This program starts all the threads going. When it hears a kill signal, it kills all the threads.
"""
import miner, peer_recieve, time, threading, tools, custom, networking, sys, api, blockchain, peers_check, multiprocessing, database, threads
#windows was complaining about lambda
def peer_recieve_func(d, DB=custom.DB):
    return peer_recieve.main(d, DB)

def main(brainwallet, pubkey_flag=False):
    DB=custom.DB
    tools.log('custom.current_loc: ' +str(custom.current_loc))
    print('starting full node')
    if not pubkey_flag:
        privkey=tools.det_hash(brainwallet)
        pubkey=tools.privtopub(privkey)
    else:
        pubkey=brainwallet

    processes= [
        {'target':tools.heart_monitor,
         'args':(DB['heart_queue'], ),
         'name':'heart_monitor'},
        {'target': blockchain.main,
         'args': (DB,),
         'name': 'blockchain'},
        {'target': api.main,
         'args': (DB, DB['heart_queue']),
         'name': 'api'},
        {'target': peers_check.main,
         'args': (custom.peers, DB),
         'name': 'peers_check'},
        {'target': miner.main,
         'args': (pubkey, DB),
         'name': 'miner'},
        {'target': networking.serve_forever,
         'args': (peer_recieve_func, custom.port, DB['heart_queue'], True),
         'name': 'peer_recieve'}
    ]
    cmds=[database.DatabaseProcess(
        DB['heart_queue'],
        custom.database_name,
        tools.log,
        custom.database_port)]
    try:
        cmds[0].start()
    except Exception as exc:
        tools.log(exc)
    tools.log('starting ' + cmds[0].name)
    time.sleep(4)
    tools.db_put('test', 'TEST')
    tools.db_get('test')
    tools.db_put('test', 'undefined')
    b=tools.db_existence(0)
    if not b:
        tools.db_put('length', -1)
        tools.db_put('memoized_votes', {})
        tools.db_put('txs', [])
        tools.db_put('peers_ranked', [])
        tools.db_put('targets', {})
        tools.db_put('times', {})
        tools.db_put('mine', False)
        tools.db_put('diffLength', '0')
    tools.db_put('stop', False)
    tools.log('stop: ' +str(tools.db_get('stop')))
    for process in processes[1:]:
        cmd=multiprocessing.Process(**process)
        cmd.start()
        cmds.append(cmd)
        tools.log('starting '+cmd.name)
    if not pubkey_flag:
        tools.db_put('privkey', privkey)
    else:
        tools.db_put('privkey', 'Default')
    tools.db_put('address', tools.make_address([pubkey], 1))
    tools.log('stop: ' +str(tools.db_get('stop')))
    while not tools.db_get('stop'):
        time.sleep(0.5)
    tools.log('about to stop threads')
    DB['heart_queue'].put('stop')
    for p in [[custom.port, '127.0.0.1'],
              [custom.api_port, '127.0.0.1']]:
        networking.connect('stop', p[0], p[1])
    cmds.reverse()
    for cmd in cmds[:-1]:
        cmd.join()
        tools.log('stopped a thread: '+str(cmd))
    time.sleep(2)
    networking.connect('stop', custom.database_port, '127.0.0.1')
    cmds[-1].join()
    tools.log('stopped a thread: '+str(cmds[-1]))
    tools.log('all threads stopped')
    sys.exit(0)
if __name__=='__main__': #for windows
    try:
        main(sys.argv[1])
    except Exception as exc:
        tools.log(exc)
