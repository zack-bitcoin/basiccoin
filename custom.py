"""This is to make magic numbers easier to deal with."""
import multiprocessing, os
try:
    from cdecimal import Decimal
except:
    from decimal import Decimal
peers = [['192.241.212.114', 7900]]#,['69.164.196.239', 8900]]
current_loc=os.path.dirname(os.path.abspath(__file__))
database_name = os.path.join(current_loc, 'DB')
log_file=os.path.join(current_loc, 'log')
port=7900
api_port=7899
database_port=7898
version = "0.0001"
max_key_length=6**4
block_reward = 10 ** 5
fee = 10 ** 3
# Lower limits on what the "time" tag in a block can say.
mmm = 100
# Take the median of this many of the blocks.
# How far back in history do we look when we use statistics to guess at
# the current blocktime and difficulty.
history_length = 400
# This constant is selected such that the 50 most recent blocks count for 1/2 the
# total weight.
inflection = Decimal('0.985')
download_many = 50  # Max number of blocks to request from a peer at the same time.
max_download = 58000
#buy_shares_target='0'*4+'1'+'9'*59
blocktime=60
DB = {
    'reward_peers_queue':multiprocessing.Queue(),
    'suggested_blocks': multiprocessing.Queue(),
    'suggested_txs': multiprocessing.Queue(),
    'heart_queue': multiprocessing.Queue(),
}


