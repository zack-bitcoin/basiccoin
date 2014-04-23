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
    if length*block_reward<premine:
        return 1
    else:
        return 1

