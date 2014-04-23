import consensus, listener, threading, custom

todo=[[consensus.mainloop, (custom.pubkey, custom.peers, custom.hashes_per_check)],
      [listener.server, ()]]
#we also need a gui
for i in todo:
    t = threading.Thread(target=i[0], args = i[1])
    t.start()
'''
consensus.mainloop(custom.pubkey, [], custom.hashes_per_check)
'''
