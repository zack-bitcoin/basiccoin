basiccoin
=====

A very simple blockchain.
Based off of the Amoveo code base. https://github.com/zack-bitcoin/amoveo

First to compile the software and start an erlang shell with the libraries loaded:
`./rebar3 shell`

Next, once the erlang shell is ready, turn on the blockchain:
`application:ensure_all_started(basiccoin).`