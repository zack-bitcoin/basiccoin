-module(recent_blocks).
-behaviour(gen_server).
-export([start_link/0,code_change/3,handle_call/3,handle_cast/2,handle_info/2,init/1,terminate/2,
         read/0, add/3]).
-include("../records.hrl").
-define(LOC, constants:recent_blocks()).
-record(r, {blocks = [], work = 0, save_limit = 0}).
%We keep a record of the blocks with the heighest accumulative difficulty so that we know what we will need to prune.
%If a fork starts from before fork_tolerance, then it would be growing from a block that is not recorded in this module. Since the data is pruned, you would be unable to maintain the database. So the node would freeze, and you would have to either restart syncing from the genesis block, or download and verify all the consensus data you don't have from the fork.
init(ok) -> 
    process_flag(trap_exit, true),
    X = db:read(?LOC),
    Ka = if 
	     X == "" -> #r{};
	     true -> X
	 end,
    {ok, Ka}.
start_link() -> gen_server:start_link({local, ?MODULE}, ?MODULE, ok, []).
code_change(_OldVsn, State, _Extra) -> {ok, State}.
terminate(_, K) -> 
    db:save(?LOC, K),
    io:fwrite("recent blocks died!\n"), 
    ok.
handle_info(_, X) -> {noreply, X}.
handle_cast(_, X) -> {noreply, X}.
handle_call({add, Hash, TotalWork, Height}, _, X) ->
    RBP = constants:recent_blocks_period(),
    R=if
          (TotalWork > X#r.work) and (Height > 0) and ((Height rem RBP) == 0) ->
	      FT = constants:fork_tolerance(),%we should look up the forth torlerance'th ancestor of the block, it's accumulative difficulty is the value we want. not Height-FT
              AB = block:get_by_height(max(0, Height - FT)),
              {ok, H} = headers:read(block:hash(AB)),
              AncestorsWork = H#header.accumulative_difficulty,
	      BS = lists:sort(fun(A, B) -> 
				      {_, A1} = A,
				      {_, B1} = B,
				      A1 < B1
			      end,
			      X#r.blocks),
              Blocks = remove_before(BS, AncestorsWork),
              %Blocks = remove_before(X#r.blocks, AncestorsWork),
              #r{blocks = [{Hash, TotalWork}|Blocks], work = TotalWork, save_limit = AncestorsWork};
          TotalWork > X#r.save_limit ->
              X#r{blocks = [{Hash, TotalWork}|X#r.blocks]};
          true -> X 
      end,
    db:save(?LOC, R),
    {reply, ok, R};
handle_call(read, _From, X) -> 
    Y = get_hashes(X#r.blocks),
    GH = block:hash(block:get_by_height(0)),
    {reply, [GH|Y], X};
handle_call(_, _From, X) -> {reply, X, X}.

get_hashes([]) -> [];
get_hashes([{Hash, _}|T]) -> 
    [Hash|get_hashes(T)].
add(Hash, Work, Height) ->
    gen_server:call(?MODULE, {add, Hash, Work, Height}).
read() -> gen_server:call(?MODULE, read).

remove_before([], _) -> [];
remove_before([{Hash, TotalWork}|T], X) when TotalWork < X ->
    KeepBlock = block:get_by_hash(Hash),
    Height = KeepBlock#block.height,
    HB = block:get_by_height(Height),
    H2 = block:hash(HB),
    if
	Height < 2 -> ok;
	H2 == Hash ->
	%true ->
	    H = KeepBlock#block.prev_hash,
	    OldBlock = block:get_by_hash(H),
	    tree_data:garbage(OldBlock, KeepBlock);
	true -> ok
    end,
    remove_before(T, X);
remove_before([H|T], X) -> [H|remove_before(T, X)].



    
