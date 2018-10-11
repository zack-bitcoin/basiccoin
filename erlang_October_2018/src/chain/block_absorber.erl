-module(block_absorber).
-behaviour(gen_server).
-include("../records.hrl").
-export([recover/1,
	 check/0,
	 save/1,    %% returns after saving
	 do_save/1]). %% run without gen_server
-export([start_link/0,init/1,handle_call/3,handle_cast/2,handle_info/2,terminate/2,code_change/3]).
init(ok) -> {ok, now()}.
start_link() -> gen_server:start_link({local, ?MODULE}, ?MODULE, ok, []).
code_change(_OldVsn, State, _Extra) -> {ok, State}.
terminate(_, _) -> 
    io:fwrite("block absorber died! \n"),
    ok.
handle_info(_, X) -> {noreply, X}.
handle_cast({doit, BP}, X) ->
    absorb_internal(BP),
    {noreply, now()}.
handle_call(check, _From, X) -> 
    {reply, X, X};
handle_call({doit, BP}, _From, X) -> 
    Y = absorb_internal(BP),
    {reply, Y, now()}.
check() -> gen_server:call(?MODULE, check).
save([]) -> ok;
save([T]) -> save(T);
save([B|T]) -> save(B), save(T);
save(X) -> 
    %io:fwrite("block absorber \n"),
    case sync:status() of
	go ->
	    gen_server:call(?MODULE, {doit, X}, 10000);
	_ -> ok
    end.
absorb_internal(error) -> error;
absorb_internal(Block) ->
    %io:fwrite("block absorber 0\n"),
    %io:fwrite(packer:pack(erlang:timestamp())),
    %io:fwrite("\n"),
    Height = Block#block.height,
    MyHeight = block:height(), %using headers gen_server
    %io:fwrite("block absorber 0.01\n"),
    %io:fwrite(packer:pack(erlang:timestamp())),
    %io:fwrite("\n"), 
    if
	Height > (MyHeight + 1) ->
	    throw("too high");
	Height < (MyHeight - 300) ->
	    throw("too low");
	true ->
	    {_, _, BH} = Block#block.trees,
	    %io:fwrite("block absorber 1\n"),
	    %io:fwrite(packer:pack(erlang:timestamp())),
	    %io:fwrite("\n"),
	    BHC = block_hashes:check(BH),%0.01
	    %io:fwrite("block absorber 1.0\n"),
	    %io:fwrite(packer:pack(erlang:timestamp())),
	    %io:fwrite("\n"),
	    NextBlock = Block#block.prev_hash,
	    %io:fwrite("block absorber 1.1\n"),
	    %io:fwrite(packer:pack(erlang:timestamp())),
	    %io:fwrite("\n"),
	    Bool = block_hashes:check(NextBlock),
	    if
		Height == 0 -> 0;
		BHC -> 3; %we already have this block
		not(Bool) -> 0;%we dont' know the previous block
		true ->
		    %io:fwrite("block absorber 1.2\n"),
		    %io:fwrite(packer:pack(erlang:timestamp())),
		    %io:fwrite("\n"),
		    false = empty == block:get_by_hash(NextBlock), %check that previous block was valid
		    %io:fwrite("block absorber 1.3\n"),
		    %io:fwrite(packer:pack(erlang:timestamp())),
		    %io:fwrite("\n"),
		    block_hashes:add(BH),%Don't waste time checking invalid blocks more than once.
		    %0.03

		    %start adding next block.
		    %io:fwrite("block absorber 1.4\n"),
		    %io:fwrite(packer:pack(erlang:timestamp())),
		    %io:fwrite("\n"),
		    {ok, H} = headers:read(BH),
		    %H = block:block_to_header(Block),%we should calculate the block hash from the header, so we don't calculate the header twice.
		    
		    %io:fwrite("block absorber 1.5\n"),
		    %io:fwrite(packer:pack(erlang:timestamp())),
		    %io:fwrite("\n"),
		    %0.3 0.09 0.1 0.08
		    %headers:absorb([H]),
		    %io:fwrite("block absorber 2\n"),
		    %io:fwrite(packer:pack(erlang:timestamp())),
		    %io:fwrite("\n"),
		    {true, Block2} = block:check(Block),%writing new block's data into the consensus state merkle trees.
		    %0.2
		    %io:fwrite("block absorber 3\n"),
		    %io:fwrite(packer:pack(erlang:timestamp())),
		    %io:fwrite("\n"),
		    do_save(Block2),%0.02
		    %io:fwrite("block absorber 4\n"),
		    %io:fwrite(packer:pack(erlang:timestamp())),
		    %io:fwrite("\n"),
		    headers:absorb_with_block([H]),%0.01
		    Header = H,
		    %io:fwrite("block absorber 5\n"),
		    %io:fwrite(packer:pack(erlang:timestamp())),
		    %io:fwrite("\n"),

		    case sync_mode:check() of
			normal -> 
			    push_block:add(Block2),
			    recent_blocks:add(BH, Header#header.accumulative_difficulty, Height),
			    %potential_block:save([], unused),
			    Txs0 = (tx_pool:get())#tx_pool.txs,
			    %TB = block:top(),
			    TWBH0 = block:hash(headers:top_with_block()),
			    TB = block:get_by_hash(TWBH0),
			    Txs = if
				      NextBlock == TWBH0 ->
					  Txs0;
				      true -> Txs0 ++ lists:reverse(tl(TB#block.txs))%if there is a small fork, re-broadcast the orphaned txs.
				  end,
			    %tx_pool:dump(Block2),
			    OldTxs = tl(Block#block.txs),
			    Keep = lists:filter(fun(T) -> not(tx_pool_feeder:is_in(testnet_sign:data(T), OldTxs)) end, Txs),%This n**2 algorithm is slow. We can make it n*log(n) by sorting both lists first, and then comparing them.
			    tx_pool_feeder:absorb_dump(Block2, lists:reverse(Keep)),
			    %tx_pool_feeder:dump(Block2),
			    %tx_pool_feeder:empty_mailbox(),
			    %tx_pool_feeder:absorb_async(lists:reverse(Keep)),
			    potential_block:dump(),
			    %spawn(fun() ->
				%	  timer:sleep(2000),
				%	  potential_block:dump()
				%  end),
			    order_book:match();
			    %sync:push_new_block(Block2);
			quick -> 
			    recent_blocks:add(BH, Header#header.accumulative_difficulty, Height),%garbage collection
			    %0.45 0.4 0.3
			    %io:fwrite("block absorber 6\n"),
			    %io:fwrite(packer:pack(erlang:timestamp())),
			    %io:fwrite("\n"),
			    tx_pool_feeder:dump(Block2),%0.08
			    %io:fwrite("block absorber 7\n"),
			    %io:fwrite(packer:pack(erlang:timestamp())),
			    %io:fwrite("\n"),
			    potential_block:dump()
		    end,
		    %io:fwrite("block absorber 9\n"),
		    %io:fwrite(packer:pack(erlang:timestamp())),
		    %io:fwrite("\n"),
		    if
			(Block2#block.height rem 10) == 0 ->
			%1 == 1 ->
			    io:fwrite("absorb block "),
			    io:fwrite(integer_to_list(Block2#block.height)),
			    io:fwrite("\n");
			true -> ok
		    end,
		    Header
	    end
    end.
do_save(BlockPlus) ->
    %found_block_timer:add(),%put it into headers instead.
    CompressedBlockPlus = zlib:compress(term_to_binary(BlockPlus)),
    Hash = block:hash(BlockPlus),
    BlockFile = utils:binary_to_file_path(blocks, Hash),
    %io:fwrite("deleting blockfile "),
    %io:fwrite(BlockFile),
    %io:fwrite("\n"),
    %file:delete(BlockFile),
    %timer:sleep(100),
    ok = db:save(BlockFile, CompressedBlockPlus).
highest_block([H|T]) ->
    B = binary_to_term(zlib:uncompress(db:read("blocks/"++H))),
    highest_block(B, T).
highest_block(B, []) -> B;
highest_block(B, [H|T]) ->
    B2 = binary_to_term(zlib:uncompress(db:read("blocks/"++H))),
    H1 = B#block.height,
    H2 = B2#block.height,
    if
	H2 > H1 -> highest_block(B2, T);
	true -> highest_block(B, T)
    end.
	    
%highest_block(B, []) -> B;
%highest_block(A, [B|C]) ->
%    D = if
%	    A#block.height > B#block.height -> A;
%	    true -> B
%	end,
%    highest_block(D, C).
first(0, _) -> [];
first(_, []) -> [];
first(N, [H|T]) -> [H|first(N-1, T)].
















recover(Mode) ->
    %sync:stop(),
    %timer:sleep(20000),
    sync_kill:start(),
    sync_mode:quick(),
    %timer:sleep(100),
    io:fwrite("recover 1\n"),
    {ok, BlockFiles} = file:list_dir("blocks/"),
    Block = case Mode of
		full ->
		    highest_block(BlockFiles);
		quick ->
		    Block1 = binary_to_term(zlib:uncompress(db:read("blocks/"++hd(BlockFiles)))),
		    L = length(BlockFiles),
		    FirstTen = if
				   L > 50 ->
				       {F, _} = lists:split(50, BlockFiles),
				       F;
				   true -> BlockFiles
			       end,
		    highest_block(Block1, tl(FirstTen))
	    end,
		    
    %TBFs = first(10, BlockFiles),
    %Blocks = lists:map(fun(BF) -> 
	%		       binary_to_term(zlib:uncompress(db:read("blocks/"++BF)))
    %end,
						%TBFs),
%Block = highest_block(hd(Blocks), tl(Blocks)),
    io:fwrite("heighest block \n"),
    io:fwrite("recover 2\n"),
    io:fwrite(integer_to_list(Block#block.height)),
    io:fwrite("is block height \n"),


    BH = Block#block.height,
    B2 = block:height(),
    Hashes = if
		 BH > B2 ->
		     [block:hash(Block)|hashes_to_root(Block)];
		 true -> []
	     end,
    io:fwrite("recover 3\n"),
    io:fwrite(integer_to_list(length(Hashes))),
    io:fwrite(" is many hashes\n"),
    %io:fwrite(packer:pack(hd(lists:reverse(Hashes)))),
    io:fwrite("\n"),
    Pid = block_organizer:pid(),
    read_absorb(lists:reverse(Hashes), Pid, []).
hashes_to_root(Block) ->
    H = Block#block.height,
    if
	((H rem 100) == 0) -> 
	    io:fwrite("reverifying block "),
	    io:fwrite(integer_to_list(H)),
	    io:fwrite("\n");
	true -> ok
    end,
    if
	H == 1 -> [];
	true ->
	    PH = Block#block.prev_hash,
	    PB = block:get_by_hash(PH),
	    [PH|hashes_to_root(PB)]
    end.
read_absorb([], _, X) -> 
    block_organizer:add(lists:reverse(X)),
    sync:start(),
    %timer:sleep(30000),
    io:fwrite("read_absorb done");
%sync_mode:check_switch_to_normal();
read_absorb(A, Pid, B) when length(B) > 20 ->
    block_organizer:add(lists:reverse(B)),
    read_absorb(A, Pid, []);
read_absorb([H|T], Pid, L) ->
    case erlang:process_info(Pid, message_queue_len) of
	undefined ->
	    timer:sleep(50),
	    read_absorb([H|T], Pid, L);
	{message_queue_len, Size} ->
	    if
		Size < 4 ->
		    B = block:get_by_hash(H),
		    read_absorb(T, Pid, [B|L]);
		true ->
		    timer:sleep(50),
		    read_absorb([H|T], Pid, L)
	    end
    end.

	    
