from get_request import request
from time import time


def assertEqual(x, y):
    if (x != y):
        print(x)
        print(y)
        throw("fail")

def test1():
    print("share blocks test 1")
    request(2, "add_peer", [[209,250,250,137],8080])
    request(2, "add_peer", [[51,15,69,135],8080])
    request(2, "add_peer", [[51,15,212,91],8080])
    request(2, "add_peer", [[159,89,106,253],8080])
    request(2, "add_peer", [[52,234,133,196],8080])

    request(2, "add_peer", [[127,0,0,1], 3010])
    request(1, "add_peer", [[127,0,0,1], 3020], 2)
    request(1, "mine_block", [1, 100000], 0.2)
    request(1, "sync", [[127,0,0,1], 3020], 0.1)
    request(2, "mine_block", [2, 100000], 10)
    #request(1, "sync", [[127,0,0,1], 3020], 0.2) # removed for propagation test.
    height1 = request(1, 'height', [], 0.05)
    height2 = request(2, 'height', [], 0.05)
    assertEqual(height1, height2)
    #we should check that the heights are the same.
def test2():
    print("share blocks test 2")
    request(1, "mine_block", [5, 100000], 3)
    request(1, "sync", [[127,0,0,1], 3020], 2)
    request(2, "sync", [[127,0,0,1], 3010], 2)#pull blocks
    request(1, "mine_block", [3, 100000], 0.02)
    #request(1, "sync", [[127,0,0,1], 3020], 0.1)#push blocks
    request(1, "spend", ["BCjdlkTKyFh7BBx4grLUGFJCedmzo4e0XT1KJtbSwq5vCJHrPltHATB+maZ+Pncjnfvt9CsCcI9Rn1vO+fPLIV4=", 100000000], 0.1)#light node 1
    request(1, "spend", ["BOnadmMfDIoCmio3ReSinirULreS3TbCEdr0R6FDDvoVB5xoAJnvwlL3yMgNhBzEb5l36z7bgizw2EKGn0W9rY8=", 200000000], 0.1)#dev3
    request(1, "spend", ["BB84LgUHDPkbXkC9p+oN+hiHN1vpsa5FjGBJTrCTxaPX0Jh/y6IXTl892GetuRAnf9VNyXc9F1hZvmr2+cJjtrA=", 100000000], 0.1)#light node 2
    request(1, "spend", ["BLgYECLeI0Iq7SZqPqhoZocy3zF3ht+fPdYkjJh3OnPU1tr7+BpDbtXGNyzDF8w4gUzV7UvM4KelK6IIvQNZZ6w=", 100000000], 0.1)
    request(1, "mine_block", [1, 100000], 0.2)
    request(1, "sync", [[127,0,0,1], 3020], 3)
    request(2, "sync", [[127,0,0,1], 3010], 1)#pull
    request(2, "sync", [[127,0,0,1], 3010], 1)#pull
    height1 = request(1, 'height', [], 0.05)
    height2 = request(2, 'height', [], 0.05)
    print("test2 1")
    assertEqual(height1, height2)
    request(2, "mine_block", [1, 100000], 0.2)
    request(2, "sync", [[127,0,0,1], 3010], 3)#push
    request(1, "sync", [[127,0,0,1], 3020], 1)#pull
    request(1, "sync", [[127,0,0,1], 3020], 3)#pull
    height1 = request(1, 'height', [], 0.05)
    height2 = request(2, 'height', [], 0.05)
    print("test2 2")
    assertEqual(height1, height2)

def add_peers(node, n, ip, port):
    if (n == 0):
        return 0
    request(node, "add_peer", [ip, port])
    return add_peers(node, n-1, ip, port+1)
    
def test3(): #test the attack where someone generates tons of fake peers and shares them like valid peers.
    print("share blocks test 3")
    request(1, "add_peer", [[127,0,0,1], 3020], 0.1)
    #add_peers(1, 20, [1,2,3,4], 2000)
    request(1, "mine_block", [1, 100000], 0.1)
    a = time()
    request(1, "sync", [], 0.1)
    b = time()
    print(b-a)

def test4():
    #someone shares a valid-looking header that has no block.
    request(1, "mine_block", [2, 0, 0], 0.1)
    request(2, "sync", [[127,0,0,1], 3010], 0.2)#pull
    request(2, "mine_block", [2, 100000], 0.1)
    request(2, "sync", [[127,0,0,1], 3010], 0.2)#push
    height1 = request(1, 'height', [], 0.05)
    height2 = request(2, 'height', [], 0.05)
    assertEqual(height1, height2)

def test5():
    request(1, "mine_block", [200, 100000], 3)
    request(2, "sync", [[127,0,0,1], 3010], 0.2)#pull
    height1 = request(1, 'height', [], 0.05)
    height2 = request(2, 'height', [], 0.05)
    assertEqual(height1, height2)
    

def share_blocks():
    test1()
    test2()
    test3()
    

if __name__ == "__main__":
    share_blocks()
