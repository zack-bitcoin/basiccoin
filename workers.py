import consensus
import listener
import multiprocessing
import custom
import leveldb
import networking
import gui
import sys

db = leveldb.LevelDB(custom.database_name)
DB = {'db': db,
      'recentHash': 0,
      'length': -1,
      'sigLength': -1,
      'txs': [],
      'suggested_blocks': [],
      'suggested_txs': [],
      'diffLength': '0'}

worker_tasks = [
    # Keeps track of blockchain database, checks on peers for new blocks and
    # transactions.
    {'target': consensus.miner,
     'args': (custom.pubkey, custom.peers, custom.hashes_per_check, DB),
     'daemon': True},
    {'target': consensus.mainloop,
     'args': (custom.peers, DB),
     'daemon': True},
    # Listens for peers. Peers might ask us for our blocks and our pool of
    # recent transactions, or peers could suggest blocks and transactions to us.
    {'target': listener.server,
     'args': (DB,),
     'daemon': True},
    {'target': gui.main,
     'args': (custom.gui_port, custom.brainwallet, DB),
     'daemon': True},
]
networking.kill_processes_using_ports([str(custom.gui_port),
                                       str(custom.listen_port)])


def start_worker_proc(**kwargs):
    print("Inithing proc.")
    is_daemon = kwargs.pop('daemon', True)
    proc = multiprocessing.Process(**kwargs)
    proc.daemon = is_daemon
    proc.start()
    return proc

workers = [start_worker_proc(**task_info) for task_info in worker_tasks]
try:
    for worker in workers:
        print("Creating worker")
        worker.join()
except KeyboardInterrupt:
    print("Exiting.")
    for worker in workers:
        worker.terminate()
    sys.exit(1)
