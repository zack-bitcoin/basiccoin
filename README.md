basiccoin

The simplest currency.

Donations: 1GbpRPE83Vjg73KFvTVZ4EnS2qNkiLY5TT

INSTALL (for ubuntu)

    sudo apt-get install git
    sudo apt-get install python-leveldb
    git clone https://github.com/zack-bitcoin/basiccoin.git
    cd basiccoin/

To run 1 node

    python workers.py

###Why do we need a simple currency

At the time of writing this there exist over 80 cryptocurrencies with market caps of over $100,000. According to Andreas Antonopolous, we will soon live in a world with millions of altcoins. It is incredibly risky to try to add new features to an old crypto. There is a high probability that you will introduce a bug. To combat this, each currency will have only one purpose.
Bitcoin currently has 40445 lines of C++ and assembly, not including gui or tests. Very few people are able to read bitcoin. It is incredibly difficulty to adapt without breaking everything. Because of how hard it is to adapt bitcoin, all the altcoins have been very simplistic. They change magic numbers, and the name, and little else.

When things get complicated, it is good to return to the basics.
The purpose of basiccoin is to be the simplest secure currency possible. Basiccoin is designed to be easily modified to create new alts.

###How do I read this?

This code is written functionally. Functions are only supposed to depend on functions that occur above them on the page. Generally people read such code starting at the bottom, because it is easier to understand the outline provided by high-level functions, instead of getting lost indetails of low-level functions.

bottom-up style explained by a master: http://paulgraham.com/progbot.html

###Why is this code so short?

http://paulgraham.com/power.html

###What are the priorities that shape coding-style?

1)  It should be a secure cryptocurrency.

2)  It should be easy to create altcoins with new features just by adding transactions types to the transactions.py file.

3)  The mental-size of a program is largely determined by how many parts of the program can alter the database. Hierarchy of who controls the blockchain:

    blockchain.db_put() and blockchain.db_delete() are low level functions that change the blockchain.
    blockchain.add_block() and blockchain.delete_block(), transactions.add_block(), and transactions.delete_block() are the only parts that use db_put and db_delete
    blockchain.add_block() and blockchain.delete_block() are the only functions that use transactions.add_block() and transactions.delete_block()
    consensus.mainloop() is the only thread which uses add_block() and delete_block().

4)  Do not allow repetitions in code.

5)  Use the name of a function or variable as the main form of commenting. If something is not clear, instead of adding comments, we just subdivide the complex task into smaller tasks, and accurately name those smaller tasks.

6)  Try to maximize number of ideas that fit on a screen at a time.

7)  pep8

###Features

*   Blockchain
*   mineable currency units
*   can create unique addresses
*   can spend the currency units to each other
*   Multisig escrow