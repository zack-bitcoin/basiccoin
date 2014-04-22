import pybitcointools as pt
listen_port=8900
version="VERSION"
block_reward=10**5
premine=10**8
fee=10**3
pubkey=pt.privtopub(pt.sha256('brain wallet'))
peers=[['localhost', 8900],['localhost', 8901]]
hashes_per_check=200000
def blocktime(length):
    #every 70 blocks, difficulty can double or half. If the blocktime has to change by x1000, this will take log2(1000)*70= about 700 blocks.
    if length*block_reward<premine:
        return 0.01#faster computer can make this number smaller and go faster. If the number gets too small, then the difficulty goes
    else:
        return 1

