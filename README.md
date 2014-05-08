basiccoin

The simplest currency. 

INSTALL (for ubuntu)

    sudo apt-get install git
    sudo apt-get install python-leveldb
    git clone https://github.com/zack-bitcoin/basiccoin.git
    cd basiccoin/

To run 1 node

    python threads.py

To quickly run 5 nodes (linux/mac only)

    ./go.sh

Then send your browser to 

    http://localhost:8701
    http://localhost:8702
    http://localhost:8703
    http://localhost:8704
    http://localhost:8705

###Why do we need a simple currency

At the time of writing this there exist over 80 cryptocurrencies with market caps of over $100,000. According to Andreas Antonopolous, we will soon live in a world with millions of altcoins. It is incredibly risky to try to add new features to an old crypto. There is a high probability that you will introduce a bug. To combat this, each currency will have only one purpose.
Bitcoin currently has 40445 lines of C++ and assembly, not including gui or tests. Very few people are able to read bitcoin. It is incredibly difficulty to adapt without breaking everything. Because of how hard it is to adapt bitcoin, all the altcoins have been very simplistic. They change magic numbers, and the name, and little else.

When things get complicated, it is good to return to the basics.
The purpose of basiccoin is to be the simplest secure currency possible. Currently about 550 lines of python, and getting smaller. Basiccoin is designed to be easily modified to create new alts.

###What are the priorities that shape coding-style?

1)  It should be a secure cryptocurrency.

2)  The part of the code that can change state is kept as small as possible. add_block and delete_block are the only functions that write to the database. The mental-size of a program is largely determined by how many parts of the program can alter the database.

3)  It should be easy to create altcoins with new features just by adding transactions types to the transactions.py file.

4)  Do not allow repetitions in code.

5)  Use the name of a function or variable as the main form of commenting. If something is not clear, instead of adding comments, we just subdivide the complex task into smaller tasks, and accurately name those smaller tasks.

6)  Try to maximize number of ideas that fit on a screen at a time.

7)  pep8

###nlocktime/spend same transaction twice problem

```javascript
//Example transaction 

{'type':'spend', 'id':pubkey1, 'to':pubkey2, 'start':1000, 'end':1200, 'count':24, 'signature':hodsnfoubewuwe==/dsnfiosfwf}
```

This transaction would be considered invalid if it was broadcast before blocklength 1000, or if it was broadcast after blocklength 1200, or if this is not pubkey1's 24th transaction.
