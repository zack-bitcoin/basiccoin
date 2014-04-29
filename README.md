NEWScoin
==========


### =======INFO ON NEWSnet=======
NewsCoin is a cryptocurrency (NEWS) and a decentralized application which supports reddit-style aggregation of user generated content. Each post and comment has its own balance. When you upvote content, you become a partial owner of it through sending NEWS to it. Every time content is upvoted you buy a stake of the post and all the early stakeholders make profit according to their stake and internal order. The currency also supports minimal marketplace functionality, and is intended to be a distributed marketplace. 

There are 2 types of employees: miners and jury-members

NewsCoin is a type of slasher currency: http://blog.ethereum.org/2014/01/15/slasher-a-punitive-proof-of-stake-algorithm/


### Types of transactions
1)spend
* include a list of pubkeys you are giving the money to, and the number of pubkeys who have to agree, in order to spend the money. (the "n" and "m" of a NxM bitcoin address)

2)mint_1
* only 1 mint transaction per block
* this gives the miner a reward.
* includes the hash of the secret.

3)mint_2
* includes the secret.
* this gives the miner a reward.
* This transaction cannot be made until at least 100 blocks after mint_1. 

4) create named account
* Now people can spend to "ganjaQueen" instead of to nonsense pubkeys like: "1847f892h4f8928294f"
* Give a menu of what goods you are selling.
* Explain the process to purchase from you. Maybe give an XMPP address for OTR chat.
* You can update your info by making a new transaction of this type.
* if a named account runs out of money, then all the reputation associated with that account is deleted.

5) buy reputation for a named account
* proof of burn

6)jury signature
* jury members sign the chain which they think is the valid chain.
* jury members have an incentive to only sign 1 chain.
* this gives the jury member a reward.
* There are about 20 constants built into the currency, examples: transaction fees, difficulty. The jury members vote to slightly adjust each of these constants upward or downward.

7)catch a cheating jury member
* if a jury member signs 2 forks, then anyone else can take those 2 signatures and make this type of transaction.
* the jury member loses their reward
* the person who created this transaction receives a reward

8)create post
* When creating a top-level post, you spend X NEWS. The value of the post is X. You own X of the post, which is all of the post.
* If your post is a comment on a different post, then it acts like an upvote and a post at the same time.

9)upvote post
* spend X NEWS
* a portion of this upvote pays the owners of the post you are upvoting, call this portion P. It includes you as one of the owners of the post, so there is an incentive to do all your investing in 1 go, instead of investing in the same post more than once.
* the post increases in value by X* (1-P)* (1-P3)
* you own the amount of the post that you increased it's value by.
* The parent posts increase in value by X* (1-P)* * 2* P3 according to the same rules.
* you own the portion of the parent post that you increased it's value by.
* The parent post's owners get paid P* X* (1-P)* p3
The goal here is for value to never be created or destroyed. (The total value of all the posts) + (the amount that owners get paid) = (amount that was invested).
* for an upvote to be valid, you need to own non-negative amount of coins at the end.

10)downvote post
* When downvoting, you spend X NEWS. 
* The post you downvoted loses X value.

### examples of transactions
   {'type':'spend', 'id':'zack', 'to':'jack', 'amount':500, 'signatures':[], 'idCount':1}
   {'type':'jurySig', 'id':'zack', 'blockHash':0000000f23h90432h, 'blockLength':11053, 'signatures':[], 'idCount':2}

idCount needs to increment every time a particular id creates a transaction. This is done so that your transactions cannot be copy/paste reused.

### Examples of what goes in the leveldb database
users are stored independently like this

   'zack':{'amount':5000000, 'pubkey':cuh4982h4c9uhr394, 'reputation':0, 'idCount':2}

Your name has to be shorter than the output of sha256().

Here is an example of how a block is stored. This is block 101.

   '101':{'transactions':[...], 'nonce':'1362784687', 'jurySigs':[...], 'difficulty':'00000000fffffffffff', 'minerSecretHash':'89fj398j38j3jf4f38j98j9s8dfwhufhs', 'merkleLCL':'8jf93j98fjp9438jf34f3', 'merkleTxs':'jc9j98ewfdp982h8dcp4hefdheuwhfrfhw', 'backup':{complex}}

when the block gets old enough, transactions can be deleted. At first jurySigs is empty, when that info is later revealed, it is put into this place. 'backup' contains the names in use on that bloack, and info about the names, and the constants on that block, and the posts on that block.

The user name "txs" is unavailable, because we use this to store zeroth confirmation transactions which will be included in the next block. 

   'txs':[{'type':'spend', 'id':'zack', 'to':'jack', 'amount':500, 'signatures':[], 'idCount':1}]

The user name "names" is unavailable because this is used to store an ordered list of every username. Maybe this isn't necessary...

   'names':['zack',...]

The user name "constants" is unavailable because this is used to store the variables in the system that the POS jury gets to vote on.

   'constants':{'usernameFee':5, 'maxPostLength':140, 'maxBlockLength':1000000, 'maxPosts':50000, ...}

The user name "root" is unavailable because this is used to store the root post:

   'root':{'message':'', 'amount':'a'}

### about posts
*  a string of characters which is limited by a maximum length. 
*  except for the root post, every post is a comment on another post. Comments have comments recursively.
*  Each post has an amount of value
*  Each post loses a chunk of its value every block.
*  there can only exist a limited number of posts at a time. If this limit is surpassed, then the least valuable post disappears. 
*  If a post dies, then all of the comments on that post die as well.
*  When posts increase in value, they pay out to the shareholders.

Here is an example post. Since this post is a child of root, it is a top-level post, and not a comment.

   'uf930h9uh39834':{'message':'I made a new cryptocurrency\nwhat do you think? ;)', 'parent':'root', 'children':[], 'amount':5000}

where 'uf930h9uh39834'=sha256(deterministic_dic2string({'message':'I made a new cryptocurrency\nwhat do you think? ;)', 'parent':'root'}))

If someone commented on our post, it would look like this:

   'ijf920fh980hsef':{'message':'no scrypt or doge?\nthis currency sucks.', 'parent':'uf930h9uh39834', 'children':[], 'amount':100}

and it would be added to the list of children of our post, like this:

   'uf930h9uh39834':{'message':'I made a new cryptocurrency\nwhat do you think? ;)', 'parent':'root', 'children':['ijf920fh980hsef'], 'amount':5000}


### positive numbers that shareholders vote on which change exponentially. (many of these numbers are rounded up to the nearest integer when they are used.)

Let f be one of these types of numbers. Lets assume that the jury member votes for f to get bigger, the new f is calculated this way:
f=f* (1+unbounded_slipperiness) where unbounded_slipperiness is a constant bounded between 0 and 1.

*  max length of a post.
*  max length of a block.
* max number of posts before we start deleting the least valuable posts. (sha256 takes too long if the input is longer than 250 million or so)
* fee every block in order to continue owning a user name or address.
* The miner fee associated to each type of transaction. (6 numbers that are each voted on independently)
* difficulty to mine next block
* The bounded_slipperiness which is used to limit by how much the bounded numbers can be changed by each jury signator

### numbers shareholders vote on that are bounded between 0 and 1

Let f be one of the numbers which must stay between 0 and 1.
Then x is the number we vote on. x's bounds are [-infinity, infinity]. Every jury signator has the ability to change x up or down by bounded_slipperiness. f is computed from x by this formula: f(x)=(atan(x)/pi)+0.5

* P1=portion of upvote that gets paid back to owners of a post
* P3=portion of comments value that the parent-post increases by. Valuable comments make posts more valuable in this way.
* P4. Every block, all the posts become less valuable. the value of the post on block n+1 is computed this way: V(n+1)=V(n)*P4
* unbounded_slipperiness which is the constant that determines how quickly we can change the unbounded numbers


### value of a post
Value = value the post started out with + value it got from upvotes - value it lost from downvotes - value it lost from age + P3*(sum of it's comment's values)

### ===databases=== 3
merkle junks in a leveldb
* blockchain
* transactions for next block go in here
potential transactions suggested to us by peers
potential blocks suggested to us by peers

### ===handshakes between nodes to maintain consensus=== 5
getinfo
* blocklength
* hash of most recent block
* number of jury signatures in chain
* maybe 10 most recent blocks?
* merkle root of transactions to be in next block (or maybe just include all the transactions) (or maybe include the nth row of the merkle tree?)
pushtx
pushblock
request blocks in range
request transactions to be included in next block #maybe make this part of getinfo

### ===threads===
* trying to mine next block
* listen for peers
* gui

### Blockchain (about 10-20 bytes per block, depending on number of jurors)
1)block's hash
2)nonce
3)jury signatures
4)difficulty
5)number that is used to deterministically choose jurors=hash256(secret) where only the miner is supposed to know the secret.
6)merkle root of the LCL
7)merkle root of transactions

### LCL=Last Closed Ledger, an idea from Ripple
Our LCL is a merkle tree. Miners need to find the merkle 
root in order to mine the next block. Jurors need
to look at the parts of this tree that change in order
to determine which block to vote on. Since they don't
have to look at the parts of the merkle tree that do
not change, jurors do not have to be full nodes.
* how much money each person has
* the value of each post/comment
* the content of each post/comment

The LCL has an interesting property. If you lose the 
proof of how much money you have, and no one else
decided to keep that proof, then not only does your
money become unspendable, it is also impossible for 
us to know how much money you lost.

Jurors only have to look at the part of the LCL that
is changing. The amount that the LCL can change is
limited by the size of the block. Blocks in bitcoin
are all smaller than 1 megabyte, so jurors will 
need less than 10 megabytes of space in order to mine
the majority of blocks.

Your computer doesn't have to be powered on until 2000 
blocks after you find out that you were selected
for jury duty.

Initial distribution:
Repeating rounds of proof-of-burn against bitcoin. 
Perhaps 12 rounds, each 1 month long. At the end of
each month, we create 1/12 of all NEWScoins
Example: In January Zack burns 2 bitcoin, and the rest of
the community burns 5 bitcoins. At the end of January, 1/12
of all coins are created, so Zack recieves 1/42 of all coins
that will be created, and the rest of the community recieves
5/84ths of all coins that will be created.
At the end of Febuary we do the same thing again. etc...