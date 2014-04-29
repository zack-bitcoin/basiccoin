import consensus, listener, threading, custom, Queue, blockchain, leveldb

DB=leveldb.LevelDB(custom.database_name)
#'''
todo=[[consensus.mainloop, (custom.pubkey, custom.peers, custom.hashes_per_check, DB), False],
      [listener.server, (DB, ), False]]
#we also need a gui
for i in todo:
    t = threading.Thread(target=i[0], args = i[1])
    t.setDaemon(i[2])
    t.start()





