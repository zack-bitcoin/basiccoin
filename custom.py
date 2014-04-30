import pybitcointools as pt
#This is for easy customization of new currencies.
database_name='DB.db'
listen_port=8900
gui_port=8700
version="VERSION"
block_reward=10**5
premine=5*10**6
fee=10**3
brainwallet='brain wallet'
privkey=pt.sha256(brainwallet)
pubkey=pt.privtopub(privkey)
peers=[['localhost', 8902],['localhost', 8901]]
hashes_per_check=2*10**4
def blocktime(length):
    if length*block_reward<premine:
        return 10#I can't get the blocks to come much quicker than 3. This needs to be optimized badly.
    else:
        return 60

