-module(sync).
-behaviour(gen_server).
-export([start_link/0,code_change/3,handle_call/3,handle_cast/2,handle_info/2,init/1,terminate/2,
	 start/1, start/0, stop/0, status/0, cron/0,
	 give_blocks/3, push_new_block/1, remote_peer/2,
	 get_headers/1, trade_txs/1, force_push_blocks/1,
	 trade_peers/1, cron/0, shuffle/1]).
-include("../records.hrl").
-define(HeadersBatch, application:get_env(amoveo_core, headers_batch)).
-define(tries, 200).%20 tries per second. 
-define(Many, 1).%how many to sync with per calling `sync:start()`
%so if this is 400, that means we have 20 seconds to download download_block_batch * download_block_many blocks
init(ok) -> 
    {ok, start}.
start_link() -> gen_server:start_link({local, ?MODULE}, ?MODULE, ok, []).
code_change(_OldVsn, State, _Extra) -> {ok, State}.
terminate(_, _) -> io:format("sync died!\n"), ok.
handle_info(_, X) -> {noreply, X}.
%handle_cast(start, _) -> {noreply, go};
%handle_cast(stop, _) -> {noreply, stop};
handle_cast({main, Peer}, _) -> 
    BL = case application:get_env(amoveo_core, kind) of
	     {ok, "production"} ->%don't blacklist peers in test mode.
		 blacklist_peer:check(Peer);
	     _ -> false
	 end,
    S = status(),
    if 
	BL -> ok;
	Peer == error -> ok;
	not(S == go) -> 
	    %io:fwrite("not syncing with this peer now "),
	    %io:fwrite(packer:pack(Peer)),
	    %io:fwrite("\n"),
	    ok;
	true ->
	    %io:fwrite("syncing with this peer now "),
	    %io:fwrite(packer:pack(Peer)),
	    %io:fwrite("\n"),
	    sync_peer(Peer),
	    case application:get_env(amoveo_core, kind) of
		{ok, "production"} ->
		    case sync_mode:check() of
			quick ->
			    timer:sleep(5000);
			normal -> ok
		    end;
		    %timer:sleep(1000);
		_ -> ok
	    end
    end,
    %spawn(fun() -> start() end),
    {noreply, []};
handle_cast(_, X) -> {noreply, X}.
%handle_call(status, _From, X) -> {reply, X, X};
handle_call(_, _From, X) -> {reply, X, X}.
status() -> sync_kill:status().
stop() -> sync_kill:stop().
start() -> start(peers:all()).
start(P) ->
    sync_kill:start(),
    %gen_server:cast(?MODULE, start),
    spawn(fun() ->
		  doit2(P)
	  end).
doit3([]) -> ok;
doit3([H|T]) ->
    gen_server:cast(?MODULE, {main, H}),
    doit3(T).
doit2([]) -> ok;
%doit2([Peer|T]) ->
doit2(L0) ->
    L = remove_self(L0),
    BH = block:height(),
    HH = api:height(),
    if
	length(L) == 0 ->
	    %io:fwrite("no one to sync with\n"),
	    ok;
	BH < HH ->
	    gen_server:cast(?MODULE, {main, hd(shuffle(L))});
	true -> 
	    %io:fwrite("nothing to sync\n"),
	    %timer:sleep(500),
	    %trade_txs(hd(shuffle(L)))
	    %sync:start()
	    ok
    end.
blocks(CommonHash, Block) ->
    BH = block:hash(Block),
    if 
        BH == CommonHash -> [];
        true ->
            PrevBlock = block:get_by_hash(Block#block.prev_hash),
            [Block|blocks(CommonHash, PrevBlock)]
    end.
give_blocks(Peer, _, _) ->
    H = headers:top(),
    HH = block:hash(H),
    {ok, FT} = application:get_env(amoveo_core, fork_tolerance),
    M = min(H#header.height, FT),
    Headers = list_headers([H], M),
    push_new_block_helper(0,0,[Peer],HH,Headers).
    %remote_peer({give_block, [block:top()]}, Peer).
   
force_push_blocks(Peer) -> 
    TheirBlockHeight = remote_peer({height}, Peer),
    CH = block:hash(block:get_by_height(TheirBlockHeight)),
    give_blocks_old(Peer, CH, TheirBlockHeight).
    
give_blocks_old(Peer, CommonHash, TheirBlockHeight) -> 
    %Common hash defaults to genesis, which makes blocks/2 super slow. This all needs to be redone.
    %io:fwrite("give blocks\n"),
    go = sync_kill:status(),
    {ok, DBB} = application:get_env(amoveo_core, push_blocks_batch),
    H = min(block:height(), max(0, TheirBlockHeight + DBB - 1)),
    Blocks0 = blocks(CommonHash, block:get_by_height(H)),
    Blocks = lists:reverse(Blocks0),
    if 
        length(Blocks) > 0 ->
	    SendHeight = (hd(Blocks0))#block.height,
            remote_peer({give_block, Blocks}, Peer),
	    timer:sleep(2000),
	    TheirBlockHeight2 = remote_peer({height}, Peer),
	    if
		(TheirBlockHeight2 > TheirBlockHeight) or (TheirBlockHeight > SendHeight) ->
	    
		    NewCommonHash = block:hash(hd(Blocks0)),
		    give_blocks(Peer, NewCommonHash, TheirBlockHeight2);
		true -> 
		    %we should remove them from the list of peers.
		    peers:remove(Peer),
		    %io:fwrite("they are not accepting our blocks."),
		    ok
	    end;
        true -> 
            %io:fwrite("finished sending blocks"),
            false
    end.

remote_peer(Transaction, Peer) ->
    case talker:talk(Transaction, Peer) of
        {ok, Return0} -> Return0;
	bad_peer -> %remove from peers, add to a black list for next N minutes.
	    {{_,_,_,_},_} = Peer,
	    %io:fwrite("removing peer "),
	    %io:fwrite(packer:pack(Peer)),
	    %io:fwrite("\n"),
	    %io:fwrite("command was "),
	    %io:fwrite(element(1, Transaction)),
	    %io:fwrite("\n"),
	    blacklist_peer:add(Peer),
	    peers:remove(Peer),
	    error;
        Return1 -> Return1
    end.
trade_peers(Peer) ->
    TheirsPeers = remote_peer({peers}, Peer),
    MyPeers = amoveo_utils:tuples2lists(peers:all()),
    remote_peer({peers, MyPeers}, Peer),
    peers:add(TheirsPeers).
get_headers(Peer) -> 
    N = (headers:top())#header.height,
    {ok, FT} = application:get_env(amoveo_core, fork_tolerance),
    Start = max(0, N - FT), 
    get_headers2(Peer, Start).
get_headers2(Peer, N) ->%get_headers2 only gets called more than once if fork_tolerance is bigger than HeadersBatch.
    {ok, HB} = ?HeadersBatch,
    Headers = remote_peer({headers, HB, N}, Peer),
    case Headers of
	error -> error;
	bad_peer -> error;
	_ ->
	    CommonHash = headers:absorb(Headers),
	    L = length(Headers),
	    case CommonHash of
		<<>> -> 
		    if 
			(L+5) > HB -> get_headers2(Peer, N+HB-1);
			true -> error%fork is bigger than fork_tolerance
		    end;
		_ -> spawn(fun() -> get_headers3(Peer, N+HB-1) end),
						%Once we know the CommonHash, then we are ready to start downloading blocks. We can download the rest of the headers concurrently while blocks are downloading.
		     CommonHash
	    end
    end.
get_headers3(Peer, N) ->
    {ok, HB} = ?HeadersBatch,
    Headers = remote_peer({headers, HB, N}, Peer),
    headers:absorb(Headers),
    if
        length(Headers) > (HB div 2) -> 
            get_headers3(Peer, N+HB-1);
        true -> ok
    end.
common_block_height(CommonHash) ->
    case block:get_by_hash(CommonHash) of
        empty -> 
            {ok, Header} = headers:read(CommonHash),
            PrevCommonHash = Header#header.prev_hash,
            common_block_height(PrevCommonHash);
        B -> B#block.height
    end.
get_blocks(Peer, N, 0, _, _) ->
    io:fwrite("could not get block "),
    io:fwrite(integer_to_list(N)),
    io:fwrite(" from peer "),
    io:fwrite(packer:pack(Peer));
get_blocks(Peer, N, Tries, Time, TheirBlockHeight) when N > TheirBlockHeight -> 
    io:fwrite("done syncing\n");
get_blocks(Peer, N, Tries, Time, TheirBlockHeight) ->
    %io:fwrite("syncing. use `sync:stop().` if you want to stop syncing.\n"),
    %io:fwrite("get blocks\n"),
    {ok, BB} = application:get_env(amoveo_core, download_blocks_batch),
    {ok, BM} = application:get_env(amoveo_core, download_blocks_many),
    timer:sleep(150),
    go = sync_kill:status(),
    Height = block:height(),
    AHeight = api:height(),
    if
	Height == AHeight -> ok;%done syncing
	((Time == second) and (N > Height + (BM * BB))) ->%This uses up 10 * BB * block_size amount of ram.
	    get_blocks(Peer, N, Tries-1, second, TheirBlockHeight);
	true ->
	    %io:fwrite("another get_blocks thread\n"),
	    Many = min(BB, TheirBlockHeight - N + 1),
	    spawn(fun() ->
			  get_blocks2(Many, N, Peer, 5)
		  end),
	    timer:sleep(100),
	    if
		Many == BB ->
		    get_blocks(Peer, N+BB, ?tries, second, TheirBlockHeight);
		true -> ok
	    end
    end.
get_blocks2(_BB, _N, _Peer, 0) ->
    %io:fwrite("get_blocks2 failed\n"),
    ok;
get_blocks2(BB, N, Peer, Tries) ->
    %io:fwrite("get blocks 2\n"),
    go = sync_kill:status(),
    Blocks = talker:talk({blocks, BB, N}, Peer),
    go = sync_kill:status(),
    Sleep = 600,
    case Blocks of
	{error, _} -> 
	    %io:fwrite("get blocks 2 failed connect error\n"),
	    %io:fwrite(packer:pack([BB, N, Peer, Tries])),
	    %io:fwrite("\n"),
	    timer:sleep(Sleep),
	    get_blocks2(BB, N, Peer, Tries - 1);
	bad_peer -> 
	    %io:fwrite("get blocks 2 failed connect bad peer\n"),
	    %io:fwrite(packer:pack([BB, N, Peer, Tries])),
	    %io:fwrite("\n"),
	    1=2;
	    %timer:sleep(Sleep),
	    %get_blocks2(BB, N, Peer, Tries - 1);
	{ok, Bs} -> block_organizer:add(Bs);
	_ -> block_organizer:add(Blocks)
    end.
remove_self(L) ->%assumes that you only appear once or zero times in the list.
    MyIP = my_ip:get(),
    {ok, MyPort} = application:get_env(amoveo_core, port),
    Me = {MyIP, MyPort},
    remove_self2(L, Me).
remove_self2([], _) -> [];
remove_self2([H|T], Me) ->
    if
	H == Me -> T;
	true -> [H|remove_self2(T, Me)]
    end.
shuffle([]) -> [];
shuffle([X]) -> [X];
shuffle(L) -> shuffle(L, length(L), []).
shuffle([], 0, Result) -> Result;
shuffle(List, Len, Result) ->
    {Elem, Rest} = nth_rest(rand:uniform(Len), List, []),
    shuffle(Rest, Len - 1, [Elem|Result]).
nth_rest(1, [E|List], Prefix) -> {E, Prefix ++ List};
nth_rest(N, [E|List], Prefix) -> nth_rest(N - 1, List, [E|Prefix]).
list_headers(X, 0) -> X;
list_headers([H|T], N) ->
    case headers:read(H#header.prev_hash) of
	error -> [H|T];
	{ok, H2}  -> %headers:read(H#header.prev_hash),
	    list_headers([H2|[H|T]], N-1)
    end.
push_new_block(Block) ->
    %keep giving this block to random peers until 1/2 the people you have contacted already know about it. Don't talk to the same peer multiple times.
    Peers0 = peers:all(),
    Peers = remove_self(Peers0),
    Hash = block:hash(Block),
    Header = block:block_to_header(Block),
    %Header = headers:top_with_block(),
    {ok, FT} = application:get_env(amoveo_core, fork_tolerance),
    M = min(Header#header.height, FT),
    Headers = list_headers([Header], M),
    {ok, Pools} = application:get_env(amoveo_core, pools),
    spawn(fun() -> push_new_block_helper(0, 0, shuffle(Pools), Hash, Headers) end),
    spawn(fun() -> push_new_block_helper(0, 0, shuffle(Peers), Hash, Headers) end).
push_new_block_helper(_, _, [], _, _) -> ok;%no one else to give the block to.
push_new_block_helper(N, M, _, _, _) when ((M > 1) and ((N*2) > (M*1))) -> ok;%the majority of peers probably already know.
push_new_block_helper(N, M, [P|T], Hash, Headers) ->
    X = remote_peer({header, Hash}, P),
    {Top, Bottom} = case X of
	    3 -> 
		{1, 1};
	    error -> {0, 0};
	    bad_peer -> {0, 0};
	    _ -> 
		spawn(fun() ->
			      remote_peer({headers, Headers}, P)
		      end),
		{0, 1}
	end,
    push_new_block_helper(N+Top, M+Bottom, T, Hash, Headers).
trade_txs(Peer) ->
    %io:fwrite("trade txs "),
    %io:fwrite(packer:pack(Peer)),
    %io:fwrite("\n"),
    case remote_peer({txs, 2, []}, Peer) of
	    error ->%once everyone upgrades to the new code, we can get rid of this branch.
	    %ok;
	    %1=2,%only for a test. remove this line.
	    spawn(fun() ->
			  Txs = remote_peer({txs}, Peer),
			  tx_pool_feeder:absorb_async(Txs)
		  end),
	    spawn(fun() ->
			  Mine = (tx_pool:get())#tx_pool.txs,
			  remote_peer({txs, lists:reverse(Mine)}, Peer)
		  end),
	    0;
	[] ->
	    spawn(fun() ->
			  TP = tx_pool:get(),
			  Checksums = remote_peer({txs, 2}, Peer),
			  MyChecksums = TP#tx_pool.checksums,
			  MyTxs = TP#tx_pool.txs,
			  Requests = checksum_minus(Checksums, MyChecksums),
			  Txs2 = remote_peer({txs, 2, Requests}, Peer),
			  tx_pool_feeder:absorb_async(Txs2),
			  SendChecksums = checksum_minus(MyChecksums, Checksums),
			  Give = ext_handler:send_txs(MyTxs, MyChecksums, SendChecksums, []),
			  remote_peer({txs, Give}, Peer)
			  
		  end)
    end.
   
sync_peer(Peer) ->
    %io:fwrite("trade peers\n"),
    spawn(fun() -> trade_peers(Peer) end),
    MyTop = headers:top(),
    %io:fwrite("get their top header\n"),
    spawn(fun() -> get_headers(Peer) end),
    {ok, HB} = ?HeadersBatch,
    {ok, FT} = application:get_env(amoveo_core, fork_tolerance),
    MyBlockHeight = block:height(),
    TheirHeaders = remote_peer({headers, HB, max(0, MyBlockHeight - FT)}, Peer),
    TheirTop = remote_peer({header}, Peer), 
    TheirBlockHeight = remote_peer({height}, Peer),
    if
	TheirTop == error -> error;
	TheirTop == bad_peer -> error;
	TheirBlockHeight == error -> error;
	TheirBlockHeight == bad_peer -> error;
	TheirHeaders == error -> error;
	TheirHeaders == bad_peer -> error;
	true ->
	    TopCommonHeader = top_common_header(TheirHeaders),
	    if
		TopCommonHeader == error -> error;
		true -> sync_peer2(Peer, TopCommonHeader, TheirBlockHeight, MyBlockHeight, TheirTop)
	    end
    end.
sync_peer2(Peer, TopCommonHeader, TheirBlockHeight, MyBlockHeight, TheirTopHeader) ->
    TTHH = TheirTopHeader#header.height,
    MTHH = (headers:top())#header.height,
    if
	TTHH < MTHH ->
	    %io:fwrite("send them headers.\n"),
	    H = headers:top(),
	    {ok, FT} = application:get_env(amoveo_core, fork_tolerance),
	    GiveHeaders = list_headers([H], FT),
	    spawn(fun() -> remote_peer({headers, GiveHeaders}, Peer) end),
	    ok;
	true -> ok
    end,
    if
        TheirBlockHeight > MyBlockHeight ->
	    %io:fwrite("get blocks from them.\n"),
	    CommonHeight = TopCommonHeader#header.height,
	    get_blocks(Peer, CommonHeight, ?tries, first, TheirBlockHeight);
	true ->
	    spawn(fun() ->
			  trade_txs(Peer)
		  end),
	    %io:fwrite("already synced with this peer \n"),
	    ok
    end.
top_common_header(L) when is_list(L) ->
    tch(lists:reverse(L));
top_common_header(_) -> error.
tch([]) -> error;
tch([H|T]) ->
    case block:get_by_hash(block:hash(H)) of
	empty -> tch(T);
	_ -> H
    end.
	    
cron() ->
    spawn(fun() ->
		  timer:sleep(4000),
		  Peers = shuffle(peers:all()),
		  LP = length(Peers),
		  if
		      LP > 0 ->
			  get_headers(hd(Peers)),
			  trade_peers(hd(Peers)),
			  timer:sleep(3000);
		      true -> ok
		  end,
		  if
		      LP > 1 ->
			  get_headers(hd(tl(Peers))),
			  trade_peers(hd(tl(Peers))),
			  timer:sleep(3000);
		      true -> ok
		  end,
		  if
		      LP > 2 ->
			  get_headers(hd(tl(tl(Peers)))),
			  trade_peers(hd(tl(tl(Peers))));
		      true -> ok
		  end
		  end),
    spawn(fun() ->
		  timer:sleep(4000),
		  cron2()
	  end).
cron2() ->
    %io:fwrite("sync cron\n"),
    SS = sync:status(),
    SC = sync_mode:check(),
    B = api:height() > block:height(),
    if 
	((SS == go) and (SC == normal)) ->
	    spawn(fun() ->
			  if 
			      B -> sync:start();
			      true -> 
				  P2 = shuffle(remove_self(peers:all())),
				  LP = length(P2),
				  if
				      LP > 0 ->
					  trade_txs(hd(P2));
				      %trade_txs(hd(tl(P2)))
				      true -> ok
				  end
			  end
		  end);
	true -> ok
    end,
    timer:sleep(5000),
    cron2().
checksum_minus([], _) -> [];
checksum_minus(A, []) -> A;
checksum_minus([A|AT], B) ->
    Bool = lists:member(A, B),
    if
	Bool -> checksum_minus(AT, B);
	true -> [A|checksum_minus(AT, B)]
    end.
	    
