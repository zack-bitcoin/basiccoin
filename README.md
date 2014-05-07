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