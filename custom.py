import pybitcointools as pt
listen_port=8900
version="VERSION"
block_reward=100000
premine=10000000
fee=10000
pubkey=pt.privtopub(pt.sha256('brain wallet'))
peers=[['localhost', 8900],['localhost', 8901]]
hashes_per_check=200000
def block_time(length):
    if length*block_reward<premine:
        return 0.01
    else:
        return 90
