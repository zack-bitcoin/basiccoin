BasicCoin
=============

A very small POW blockchain

This software is not a secure blockchain. It is a model to help learn how blockchains work.
I am mostly work on this blockchain, which is actually designed to be secure: https://github.com/BumblebeeBat/FlyingFox

None of my python blockchains are secure because it is possible to send messages to them that make them crash. It is far easier to write Erlang code that wont crash than python code that wont crash.


Donations: 1GbpRPE83Vjg73KFvTVZ4EnS2qNkiLY5TT

=====INSTALL 

    sudo pip2 install m3-cdecimal #for Mac use pip instead of pip2
    sudo pip install leveldb
    #software can run without cdecimal, but it is slower.
    git clone https://github.com/zack-bitcoin/basiccoin.git
    cd basiccoin

====RUN A NODE

    python2.7 cli.py start

It will take time to download the blockchain.

====TALK TO THE NODE

    python2.7 cli.py
