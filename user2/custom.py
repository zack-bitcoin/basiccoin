import pybitcointools as pt
#This is for easy customization of new currencies.
database_name='DB.db'
listen_port=8902
gui_port=8702
version="VERSION"
block_reward=10**5
premine=5*10**6
fee=10**3
brainwallet='brain wallet 2'
privkey=pt.sha256(brainwallet)
pubkey=pt.privtopub(privkey)
peers=[['localhost', 8901],['localhost', 8902],['localhost', 8903],['localhost', 8904],['localhost', 8905]]
hashes_per_check=10**5
def blocktime(length):
    if length*block_reward<premine:
        return 30#I can't get the blocks to come much quicker than 3. This needs to be optimized badly.
    else:
        return 60

