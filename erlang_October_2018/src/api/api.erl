-module(api).
-compile(export_all).
-include("../records.hrl").
test() -> {test_response}.
balance() ->
    A = account(),
    case A of
        empty -> 0;
        A -> A#account.balance
    end.
account() -> account(keys:pubkey()).
account(P) ->
    Pubkey = decode_pubkey(P),
    trees:dict_tree_get(accounts, Pubkey).
decode_pubkey(P) when size(P) == 65 -> P;
decode_pubkey(P) when is_list(P) -> 
    decode_pubkey(base64:decode(P));
decode_pubkey(P) when ((size(P) > 85) and (size(P) < 90)) -> 
    decode_pubkey(base64:decode(P)).
pubkey() -> base64:encode(keys:pubkey()).
add_peer(IP, Port) ->
    peers:add({IP, Port}),
    0.
sync() -> 
    spawn(fun() -> sync:start() end),
    0.
sync(IP, Port) -> 
    spawn(fun() -> sync:start([{IP, Port}]) end),
    0.
sync(2, IP, Port) ->
    spawn(fun() -> sync:get_headers({IP, Port}) end),
    0.
mine(1) ->
    mine:start(),
    0;
mine(2) ->
    mine:stop(),
    0.
break() ->    
    1=2.
spend(ID0, Amount) ->
    ID = decode_pubkey(ID0),
    K = keys:pubkey(),
    if 
	ID == K -> io:fwrite("you can't spend money to yourself\n");
	true -> 
	    Tx = spend_tx:make_dict(ID, Amount, constants:burn_fee(), keys:pubkey()),
	    tx_maker0(Tx)
    end.
tx_maker0(Tx) -> 
    case keys:sign(Tx) of
	{error, locked} -> 
	    io:fwrite("your password is locked. use `keys:unlock(\"PASSWORD1234\")` to unlock it"),
	    ok;
	Stx -> 
	    tx_pool_feeder:absorb(Stx),
	    hash:doit(Tx)
    end.

stop() ->
    basiccoin_sup:stop(),
    ok = application:stop(basiccoin),
    io:fwrite("stopping node\n").
