basiccoin
=====

A very simple blockchain.
Based off of the Amoveo code base. https://github.com/zack-bitcoin/amoveo

A work in progress. This is not yet a functioning blockchain.

basiccoin = amoveo - (oracles and channels).

First, to compile the software and start an erlang shell with the libraries loaded:
`./rebar3 shell`

Next, once the erlang shell is ready, turn on the blockchain:
`utils:start().`

If you want to make txs, you need to unlock your keys:
`keys:unlock("").`

After you finish syncing the blocks, switch to sync mode normal before mining.
`sync_mode:normal().`
you also need sync_mode normal for running tests.

To turn off your node, first turn off syncing if it is on:
`sync:stop()`.
then turn the node off:
`api:stop().`



Design
=======

This is designed with this order of priorities:
1) it should be secure
2) it should be scalable
3) it should be small

We wanted it to be secure and scalable so that people would be able to reuse this code in other projects.
We wanted it to be small so that it is easy to read the code and understand what is going on.
