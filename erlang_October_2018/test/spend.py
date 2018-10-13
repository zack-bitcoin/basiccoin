from get_request import request

def spend_test():
    print("spend test")
    pub2 = "BGRv3asifl1g/nACvsJoJiB1UiKU7Ll8O1jN/VD2l/rV95aRPrMm1cfV1917dxXVERzaaBGYtsGB5ET+4aYz7ws="
    pub1 = "BIVZhs16gtoQ/uUMujl5aSutpImC4va8MewgCveh6MEuDjoDvtQqYZ5FeYcUhY/QLjpCBrXjqvTtFiN4li0Nhjo="
    priv = "nJgWyLTX1La8eCbPv85r3xs7DfmJ9AG4tLrJ5fiW6qY="
    brainwallet = ''
    request(1, "mine_block", [1,100000], 0.1)
    request(1, "mine_block", [1,100000], 0.1)
    request(1, "sync", [[127,0,0,1], 3020], 5)
    request(2, "load_key", [pub2, priv, brainwallet], 1)
    request(1, "create_account", [pub2, 1], 0.1)
    request(1, "sync", [[127,0,0,1], 3020], 0.1)
    request(1, "spend", [pub2, 2])
    request(1, "spend", [pub2, 3])
    request(1, "spend", [pub2, 1])
    request(1, "spend", [pub2, 100000000])#1 veo
    request(1, "sync", [[127,0,0,1], 3020], 0.2)
    #request(2, "sync", [[127,0,0,1], 3010], 0.2)
    #request(1, "sync", [[127,0,0,1], 3020], 0.1)
    request(1, "mine_block", [1,100000], 0.1)
#def dont_toit():
    pub1 = "BIVZhs16gtoQ/uUMujl5aSutpImC4va8MewgCveh6MEuDjoDvtQqYZ5FeYcUhY/QLjpCBrXjqvTtFiN4li0Nhjo="
    request(2, "sync", [2, [127,0,0,1], 3010], 0.4)#get headers
    request(2, "sync", [[127,0,0,1], 3010], 0.8)
    request(2, "spend", [pub1, 10000000])# 0.1 veo
    request(2, "mine_block", [1,100000], 0.1)
    request(1, "sync", [2, [127,0,0,1], 3020], 0.2)#get headers
    request(1, "sync", [[127,0,0,1], 3020], 0.1)
    request(1, "mine_block", [1,100000], 0.1)
    request(1, "mine_block", [1,100000], 0.1)
    request(1, "mine_block", [1,100000], 0.5)
    request(2, "sync", [2, [127,0,0,1], 3010], 0.1)
    request(2, "sync", [[127,0,0,1], 3010])
def multi_spend():
    request(1, "mine_block", [10,100000], 0.5)
    pub2 = "BGRv3asifl1g/nACvsJoJiB1UiKU7Ll8O1jN/VD2l/rV95aRPrMm1cfV1917dxXVERzaaBGYtsGB5ET+4aYz7ws="
    pub3 = "BJEQ6xCEdsGVUte/eECZ5FkmjNkhVuThIirSIrfMhUpN68PcjKM39uKalFEs2Curl2PVqv+WBDIDmYKjHl/NW8I="
    pub1 = "BIVZhs16gtoQ/uUMujl5aSutpImC4va8MewgCveh6MEuDjoDvtQqYZ5FeYcUhY/QLjpCBrXjqvTtFiN4li0Nhjo="
    request(1, "spend", [[-6, [700, pub2], [650, pub3]]])
    request(1, "mine_block", [1,100000], 0.5)
    request(1, "spend", [[-6, [550, pub3]]])
    request(1, "mine_block", [1,100000], 0.5)


if __name__ == "__main__":
    spend_test()
    multi_spend()
