"""This is to make magic numbers easier to deal with."""
import tools, hashlib
peers = [['127.0.0.1', 8900]]
database_name = 'DB.db'
port=8901
basicd_port=8801
version = "VERSION"
block_reward = 10 ** 5
premine = 5 * 10 ** 6
fee = 10 ** 3
# Lower limits on what the "time" tag in a block can say.
mmm = 100
# Take the median of this many of the blocks.
# How far back in history do we look when we use statistics to guess at
# the current blocktime and difficulty.
history_length = 400
# This constant is selected such that the 50 most recent blocks count for 1/2 the
# total weight.
inflection = 0.985
download_many = 50  # Max number of blocks to request from a peer at the same time.
max_download = 50000
def blocktime(length): return 30
