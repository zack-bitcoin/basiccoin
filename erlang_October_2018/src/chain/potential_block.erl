-module(potential_block).
-behaviour(gen_server).
-export([start_link/0,code_change/3,handle_call/3,handle_cast/2,handle_info/2,init/1,terminate/2]).
%This module keeps track of what might become the next block of the blockchain, if you are mining or running a mining pool.
-export([new/0, read/0, save/0, dump/0, check/0, save/2]).
%-define(potential_block, "data/potential_blocks.db").
-define(refresh_period, 60).%how often we check if there are new txs that can be included in the block. in seconds
-include("../../records.hrl").
-record(pb, {block, time}).
init(ok) -> 
    process_flag(trap_exit, true),
    Z = #pb{block = "", time = now()},
    {ok, Z}.
start_link() -> gen_server:start_link({local, ?MODULE}, ?MODULE, ok, []).
code_change(_OldVsn, State, _Extra) -> {ok, State}.
terminate(_, X) -> 
    TP = tx_pool:get(),
    Txs = TP#tx_pool.txs,
    tx_pool:dump(),
    spawn(fun() ->
		  timer:sleep(1000),
		  tx_pool_feeder:absorb_async(Txs)
	  end),
    io:format("potential block died!"), ok.
handle_info(_, X) -> {noreply, X}.
handle_cast(_, X) -> {noreply, X}.
handle_call(dump, _, _) -> 
    {reply, ok, #pb{block = "", time = now()}};
handle_call({save, Txs, _Height}, _, _) -> 
    Top = headers:top_with_block(),
    PB = block:get_by_hash(block:hash(Top)),
    Block = block:make(Top, Txs, PB#block.trees, keys:pubkey()),
    {reply, ok, #pb{block = Block, time = now()}};
handle_call(save, _, _) -> 
    Block = new_internal(""),
    {reply, ok, #pb{block = Block, time = now()}};
handle_call(new, _, Old) -> 
    Block = new_internal(Old#pb.block),
    {reply, ok, #pb{block = Block, time = now()}};
handle_call(check, _From, X) -> 
    {reply, X#pb.block, X};
handle_call(read, _From, X) -> 
    D = delta(X#pb.time, now()),
    %D = timer:now_diff(now(), X#pb.time) div 1000000,
    B = X#pb.block,
    BH = case B of
	     "" -> 0;
	     _ -> B#block.height
	 end,
    TP = tx_pool:get(),
    NH = TP#tx_pool.height,
    Y = if
	    B == "" ->
		#pb{block = new_internal2(TP), time = now()};
	    (not (BH == (NH + 1))) ->%block height changed
		#pb{block = new_internal2(TP), time = now()};
	    (D < ?refresh_period) -> X;%only update txs once every refresh period.
	    true ->
		NewTxs = TP#tx_pool.txs,
		CurrentTxs = B#block.txs,
		TxChanged = tx_changed(NewTxs, CurrentTxs),
		if
		    TxChanged ->%if txs have changed
			#pb{block = new_internal(B, TP), time = now()};
		    true -> X#pb{time = now()}
		end
	end,
    {reply, Y#pb.block, Y};
handle_call(_, _From, X) -> {reply, X, X}.
delta({A, B, _}, {D, E, _}) ->%start, end
    C = (A*1000000) + B,
    F = (D*1000000) + E,
    F - C.
new() -> gen_server:call(?MODULE, new).
save() -> gen_server:call(?MODULE, save).
save(Txs, Height) -> gen_server:call(?MODULE, {save, Txs, Height}).
dump() -> gen_server:call(?MODULE, dump).
read() -> gen_server:call(?MODULE, read).
check() -> gen_server:call(?MODULE, check).
new_internal(Old, TP) ->
    PH = Old#block.prev_hash,
    PB = block:get_by_hash(PH),
    %spawn(fun() ->
	%	  tree_data:garbage(Old, PB)
	%  end),
    new_internal2(TP).
new_internal("") ->
    TP = tx_pool:get(),
    new_internal2(TP);
new_internal(Old) ->
    TP = tx_pool:get(),
    new_internal(Old, TP).
new_internal2(TP) ->
    Txs = TP#tx_pool.txs,
    T = TP#tx_pool.height,
    %B = api:height() == T,
    B = true,
    if
	B ->
    %timer:sleep(200),
	    PB = block:get_by_height(T),
	    if
		PB == empty -> "";
		true ->
		    Top = block:block_to_header(PB),%it would be way faster if we had a copy of the block's hash ready, and we just looked up the header by hash.
    %Top = headers:top_with_block(),
    %PB = block:get_by_hash(block:hash(Top)),
		    block:make(Top, Txs, PB#block.trees, keys:pubkey())
	    end;
	true -> ""
    end.
tx_changed(New, Old) ->    
    N2 = tx_det_order(New),
    O2 = tx_det_order(Old),
    not(N2 == O2).
tx_det_order(L) -> lists:sort(L).
    
