-module(tx_pool_feeder).
-behaviour(gen_server).
-export([start_link/0,init/1,handle_call/3,handle_cast/2,handle_info/2,terminate/2,code_change/3, absorb_dump/2]).
-export([absorb/1, absorb_async/1, absorb_unsafe/1, is_in/2,
	 empty_mailbox/0, dump/1]).
-include("../records.hrl").
start_link() -> gen_server:start_link({local, ?MODULE}, ?MODULE, ok, []).
init(ok) -> 
    %process_flag(trap_exit, true),
    {ok, []}.
handle_call({absorb, SignedTx}, _From, State) ->
    case absorb_internal(SignedTx) of
	error -> ok;
	NewDict ->
	    dict:find(sample, NewDict),
	    tx_pool:absorb_tx(NewDict, SignedTx)
    end,
    {reply, ok, State};
handle_call(empty_mailbox, _, S) -> 
    {reply, ok, S};
handle_call(_, _, S) -> {reply, S, S}.
handle_cast({dump, Block}, S) -> 
    tx_pool:dump(Block),
    {noreply, S};
handle_cast({absorb, SignedTxs}, S) -> 
    ai2(SignedTxs),
    {noreply, S};
handle_cast({absorb_dump, Block, SignedTxs}, S) -> 
    tx_pool:dump(Block),
    ai2(SignedTxs),
    {noreply, S};
handle_cast(_, S) -> {noreply, S}.
handle_info(_, S) -> {noreply, S}.
terminate(_, _) -> 
    ok.
    %io:fwrite("tx_pool_feeder died\n").
code_change(_, S, _) -> {ok, S}.
is_in(_, []) -> false;
is_in(Tx, [STx2 | T]) ->
    Tx2 = testnet_sign:data(STx2),
    (Tx == Tx2) orelse (is_in(Tx, T)).
absorb_internal(SignedTx) ->
    S = self(),
    Wait = case application:get_env(amoveo_core, kind) of
	       {ok, "production"} -> 200;
	       _ -> 1000
	   end,
    spawn(fun() ->
		  absorb_internal2(SignedTx, S)
	  end),
    receive
	X -> X
    after 
	Wait -> 
	    io:fwrite("dropped a tx\n"),
	    io:fwrite(packer:pack(SignedTx)),
	    io:fwrite("\n"),
	    error
    end.
	    
	    
absorb_internal2(SignedTx, PID) ->
    Tx = testnet_sign:data(SignedTx),
    F = tx_pool:get(),
    Txs = F#tx_pool.txs,
    case is_in(Tx, Txs) of
        true -> PID ! error;
        false -> 
	    true = testnet_sign:verify(SignedTx),
	    Fee = element(4, Tx),
	    Type = element(1, Tx),
	    {ok, MinimumTxFee} = application:get_env(amoveo_core, minimum_tx_fee),
	    MinimumTxFee = constants:minimum_tx_fee(),
	    true = Fee > MinimumTxFee,
	    X = absorb_unsafe(SignedTx),
	    PID ! X
    end.
    
grow_dict(Dict, [], _) -> Dict;
grow_dict(Dict, [{TreeID, Key}|T], Trees) ->
    TreeID = accounts,
    Dict2 = 
	case dict:find({TreeID, Key}, Dict) of
	    error ->
		Tree = trees:TreeID(Trees),
		{_, Val, _} = TreeID:get(Key, Tree),
		Val2 = case Val of
			   empty -> 0;
			   X -> TreeID:serialize(X)
		       end,
		Foo = Val2,
		dict:store({TreeID, Key}, Foo, Dict);
	    {ok, _} -> Dict
	end,
    grow_dict(Dict2, T, Trees).

	    
absorb_unsafe(SignedTx, Trees, Height, Dict) ->
    %This is the most expensive part of absorbing transactions.
    Querys = proofs:txs_to_querys([SignedTx], Trees, Height + 1),
    %Querys is a list like [[TreeID, Key]...]
    %for every query, check if it is in the dict already.
    %If it is already in the dict, then we are done.
    %Otherwise, get a copy from the tree, and store it in the dict.
    Dict2 = grow_dict(Dict, Querys, Trees),
    txs:digest_from_dict([SignedTx], Dict2, Height + 1).%This processes the tx.
ai2([]) -> ok;
ai2([H|T]) ->
    case absorb_internal(H) of
	error -> ok;
	NewDict ->
	    dict:find(sample, NewDict),
	    tx_pool:absorb_tx(NewDict, H)
    end,
    ai2(T).
    
empty_mailbox() -> gen_server:call(?MODULE, empty_mailbox).
absorb([]) -> ok;%if one tx makes the gen_server die, it doesn't ignore the rest of the txs.
absorb([H|T]) -> absorb(H), absorb(T);
absorb(SignedTx) ->
    N = sync_mode:check(),
    case N of
	normal -> 
	    gen_server:call(?MODULE, {absorb, SignedTx});
	_ -> %io:fwrite("warning, transactions don't work well if you aren't in sync_mode normal")
	    ok
    end.
absorb_async(SignedTxs) ->
    N = sync_mode:check(),
    case N of
	normal -> 
	    gen_server:cast(?MODULE, {absorb, SignedTxs});
	_ -> %io:fwrite("warning, transactions don't work well if you aren't in sync_mode normal")
	    ok
    end.
absorb_dump(Block, STxs) ->
    N = sync_mode:check(),
    case N of
	normal -> 
	    gen_server:cast(?MODULE, {absorb_dump, Block, STxs});
	_ -> ok
    end.
absorb_unsafe(SignedTx) ->
    F = tx_pool:get(),
    Trees = F#tx_pool.block_trees,
    Height = F#tx_pool.height,
    Dict = F#tx_pool.dict,
    absorb_unsafe(SignedTx, Trees, Height, Dict).
dump(Block) ->
    gen_server:cast(?MODULE, {dump, Block}).
