import consensus, listener, threading, custom, blockchain, leveldb, gui, networking, time, sys

db=leveldb.LevelDB(custom.database_name)
DB={'db':db, 
    'recentHash':0, 
    'length':-1, 
    'sigLength':-1, 
    'txs':[], 
    'suggested_blocks':[], 
    'suggested_txs':[], 
    'diffLength':'0'}
todo=[
#keeps track of blockchain database, checks on peers for new 
#blocks and transactions.
    [consensus.miner, 
     (custom.pubkey, custom.peers, custom.hashes_per_check, DB), True],
    [consensus.mainloop, 
     (custom.peers, DB), True],
#listens for peers. Peers might ask us for our blocks and our pool of recent 
#transactions, or peers could suggest blocks and transactions to us.
      [listener.server, (DB, ), True],
      [gui.main, (custom.gui_port, custom.brainwallet, DB), True]]
networking.kill_processes_using_ports([str(custom.gui_port),
                                       str(custom.listen_port)])
for i in todo:
    t = threading.Thread(target=i[0], args = i[1])
    t.setDaemon(i[2])
    t.start()

while True:
    try:
        time.sleep(1)
    except KeyboardInterrupt:
        print('exiting')
        sys.exit(1)
    
