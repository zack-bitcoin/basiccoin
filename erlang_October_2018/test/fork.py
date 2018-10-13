from get_request import request

def assertEqual(x, y):
    if (x != y):
        print(x)
        print(y)
        throw("fail")

def test_mine_and_sync():
    print("fork test: mine and sync test")
    request(2, "add_peer", [[127,0,0,1], 3010], 5)
    request(2, "add_peer", [[127,0,0,1], 3010])
    request(2, "add_peer", [[127,0,0,1], 3030])
    request(1, "add_peer", [[127,0,0,1], 3020])
    request(1, "add_peer", [[127,0,0,1], 3030])
    request(1, "add_peer", [[127,0,0,1], 3020])
    request(1, "add_peer", [[127,0,0,1], 3010])
    request(2, 'sync', [[127,0,0,1], 3010], 0.1)
    request(1, 'sync', [[127,0,0,1], 3020], 0.1)
    request(1, 'mine_block', [2, 100000], 1)
    request(2, 'sync', [[127,0,0,1], 3010], 1)
    request(2, 'mine_block', [12, 100000], 0)
    request(1, 'mine_block', [11, 100000], 5)
    request(2, 'sync', [[127,0,0,1], 3010], 0.5)
    request(1, 'sync', [[127,0,0,1], 3030], 0.3)
    request(3, 'sync', [[127,0,0,1], 3010], 0.3)
    height1 = request(1, 'height', [], 0.05)
    height2 = request(2, 'height', [], 0.05)
    height3 = request(3, 'height', [], 0.05)
    assertEqual(height1, height2)
    assertEqual(height1, height3)
    #assertEqual(height1, "[\"ok\",4]")
    
def test_three():
    print("fork test: sync three nodes test")
    request(1, 'mine_block', [1, 1000000], 1.5)
    request(2, 'sync', [[127,0,0,1], 3010], 0.3)
    request(3, 'sync', [[127,0,0,1], 3010], 0.5)
    request(2, 'mine_block', [1, 1000000], 0)
    request(1, 'mine_block', [2, 1000000], 2)
    request(3, 'sync', [[127,0,0,1], 3010], 0.3)
    request(3, 'sync', [[127,0,0,1], 3020], 0.3)
    height1 = request(1, 'height', [], 0.05)
    height2 = request(2, 'height', [], 0.05)
    assertEqual(height1, height2)

def test_orphan_txs():
    pub2 = "BGRv3asifl1g/nACvsJoJiB1UiKU7Ll8O1jN/VD2l/rV95aRPrMm1cfV1917dxXVERzaaBGYtsGB5ET+4aYz7ws="
    request(1, "spend", [pub2, 1], 1)
    request(1, "spend", [pub2, 1], 1)
    request(1, 'txs', [[127,0,0,1], 3020], 1)
    request(1, "spend", [pub2, 1], 1)
    request(1, "spend", [pub2, 1], 1)
    #request(1, 'mine_block', [1, 1000000], 0)
    request(2, 'mine_block', [1, 1000000], 1)
    request(2, 'mine_block', [1, 1000000], 1)
    request(2, 'sync', [[127,0,0,1], 3010], 0.3)
    request(1, 'sync', [[127,0,0,1], 3020], 0.5)
    request(1, 'sync', [2, [127,0,0,1], 3020], 0.5)
    request(2, "add_peer", [[127,0,0,1], 3010])
    request(1, "add_peer", [[127,0,0,1], 3020])

    


if __name__ == "__main__":
    test_mine_and_sync()
    test_three()
    #test_orphan_txs()
