-module(headers).
-behaviour(gen_server).
-export([absorb/1, absorb_with_block/1, read/1, read_ewah/1, top/0, dump/0, top_with_block/0,
         make_header/8, serialize/1, deserialize/1,
         difficulty_should_be/2, 
	 ewah_range/2,
	 test/0]).
-export([start_link/0,init/1,handle_call/3,handle_cast/2,handle_info/2,terminate/2,code_change/3]).
-include("../records.hrl").
-define(LOC, constants:headers_file()).
-record(s, {headers = dict:new(),
            top = #header{},
	    top_with_block = #header{}
	   }).
init([]) ->
    process_flag(trap_exit, true),
    X = db:read(?LOC),
    K = if
	    X == "" -> 
                empty_data();
	    true -> X
	end,
    {ok, K}.
start_link() ->
    gen_server:start_link({local, ?MODULE}, ?MODULE, [], []).
handle_call({read_ewah, Hash}, _From, State) ->
    Header = dict:find(Hash, State#s.headers),
    {reply, Header, State};
handle_call({read, Hash}, _From, State) ->
    A = case dict:find(Hash, State#s.headers) of
	    error -> error;
	    {ok, {Header, _}} -> {ok, Header};
	    {ok, Header} -> {ok, Header}
	end,
    {reply, A, State};
handle_call({check}, _From, State) ->
    {reply, State, State};
handle_call({dump}, _From, _State) ->
    {reply, ok, empty_data()};
handle_call({top_with_block}, _From, State) ->
    {reply, State#s.top_with_block, State};
handle_call({top}, _From, State) ->
    {reply, State#s.top, State};
handle_call({add_with_block, Hash, Header}, _From, State) ->
    AD = Header#header.accumulative_difficulty,
    Top = State#s.top_with_block,
    AF = Top#header.accumulative_difficulty,
    NewTop = case AD >= AF of
                 true -> 
		     found_block_timer:add(),
		     Header;
                 false -> Top
        end,
    %Headers = dict:store(Hash, Header, State#s.headers),
    {reply, ok, State#s{top_with_block = NewTop}};
handle_call({add, Hash, Header, EWAH}, _From, State) ->
    AD = Header#header.accumulative_difficulty,
    Top = State#s.top,
    AF = Top#header.accumulative_difficulty,
    NewTop = case AD >= AF of
                 true -> Header;
                 false -> Top
        end,
    Headers = dict:store(Hash, {Header, EWAH}, State#s.headers),
    {reply, ok, State#s{headers = Headers, top = NewTop}}.
handle_cast(_, State) ->
    {noreply, State}.
handle_info(_Info, State) ->
    {noreply, State}.
terminate(_Reason, X) ->
    db:save(?LOC, X),
    io:fwrite("headers died!\n"),
    ok.
code_change(_OldVsn, State, _Extra) ->
    {ok, State}.

check() -> gen_server:call(?MODULE, {check}).

absorb_with_block([]) -> 0;
absorb_with_block([F|T]) when is_binary(F) ->
    absorb([deserialize(F)|T]);
absorb_with_block([F|T]) ->
    Hash = block:hash(F),
    %false = empty == block:get_by_hash(Hash),
    ok = gen_server:call(?MODULE, {add_with_block, Hash, F}),
    absorb_with_block(T).
absorb(X) -> 
    absorb(X, block:hash(block:get_by_height(0))).
absorb([], CommonHash) -> 
    CommonHash;
absorb([First|T], R) when is_binary(First) ->
    A = deserialize(First),
    absorb([A|T], R);
absorb([Header | T], CommonHash) ->
    Bool = Header#header.difficulty >= constants:initial_difficulty(),
    if
	not(Bool) -> 
	    io:fwrite(Bool),
	    io:fwrite("\n"),
	    io:fwrite(integer_to_list(Header#header.difficulty)),
	    io:fwrite("\n"),
	    io:fwrite(integer_to_list(constants:initial_difficulty())),
	    io:fwrite("\n"),
	    1=2,
	    ok;%we should delete the peer that sent us this header.
	true ->
	    Hash = block:hash(Header),
	    case read(Hash) of
		{ok, _} -> 
		    absorb(T, Hash); %don't store the same header more than once.
		error ->
		    case check_pow(Header) of
			false -> io:fwrite("invalid header without enough work\n"),
				 1=2,
				 ok;
			true ->
		      %check that there is enough pow for the difficulty written on the block
			    case read(Header#header.prev_hash) of
				error -> 
				    io:fwrite("don't have a parent for this header\n"),
				    1=2,
				    error;
				{ok, _} ->
				    case check_difficulty(Header) of%check that the difficulty written on the block is correctly calculated
					{true, _, EWAH} ->
					    %io:fwrite("\n"),
					    %io:fwrite("add ewah "),
					    %io:fwrite(integer_to_list(EWAH)),
					    %io:fwrite("\n"),
					    %io:fwrite("now "),
					    %io:fwrite(packer:pack(erlang:timestamp())),
					    %io:fwrite("\n"),
					    gen_server:call(?MODULE, {add, Hash, Header, EWAH}),
					    absorb(T, CommonHash);
					X -> 
					    io:fwrite(X),
					    1=2,
					    io:fwrite("incorrectly calculated difficulty\n")
				    end
			    end
		    end
	    end
    end.
check_pow(Header) ->
    MineDiff = Header#header.difficulty,
    Data = block:hash(Header#header{nonce = <<0:256>>}),
    <<Nonce:256>> = Header#header.nonce,
    pow:check_pow({pow, Data, MineDiff, Nonce}, constants:hash_size(), 1).

check_difficulty(A) ->
    {B, EWAH} = case A#header.height < 2 of
            true ->
                {constants:initial_difficulty(), 1000000};
            false ->
                {ok, PHeader} = read(A#header.prev_hash),
                difficulty_should_be(A, PHeader)
        end,
    {B == A#header.difficulty, B, EWAH}.
read(Hash) -> gen_server:call(?MODULE, {read, Hash}).
read_ewah(Hash) -> gen_server:call(?MODULE, {read_ewah, Hash}).
top() -> gen_server:call(?MODULE, {top}).
top_with_block() -> gen_server:call(?MODULE, {top_with_block}).
dump() -> gen_server:call(?MODULE, {dump}).
make_header(PH, 0, Time, Version, TreesHash, TxsProofHash, Nonce, Difficulty) ->
    #header{prev_hash = PH,
	    height = 0, 
	    time = Time, 
	    version = Version,
	    trees_hash = TreesHash,
	    txs_proof_hash = TxsProofHash,
	    nonce = <<Nonce:256>>,
	    difficulty = Difficulty,
	    accumulative_difficulty = 0};
make_header(PH, Height, Time, Version, Trees, TxsProodHash, Nonce, Difficulty) ->
    AC = case read(PH) of
            {ok, PrevHeader} ->
                pow:sci2int(Difficulty) + 
                     PrevHeader#header.accumulative_difficulty;
            _ -> Height %the parent is unknown
        end,
    #header{prev_hash = PH,
            height = Height,
            time = Time,
            version = Version,
            trees_hash = Trees,
            txs_proof_hash = TxsProodHash,
	    nonce = <<Nonce:256>>,
            difficulty = Difficulty,
            accumulative_difficulty = AC}.
serialize(H) ->
    false = H#header.prev_hash == undefined,
    HtB = constants:height_bits(),
    TB = constants:time_bits(),
    VB = constants:version_bits(),
    DB = 16,
    HB = constants:hash_size()*8,
    HB = bit_size(H#header.prev_hash),
    HB = bit_size(H#header.trees_hash),
    HB = bit_size(H#header.txs_proof_hash),
    HB = bit_size(H#header.nonce),
    <<(H#header.prev_hash)/binary,
     (H#header.height):HtB,
     (H#header.time):TB,
     (H#header.version):VB,
     (H#header.trees_hash)/binary,
     (H#header.txs_proof_hash)/binary,
     (H#header.difficulty):DB,
     (H#header.nonce)/binary
    >>.
deserialize(H) ->
    HB = constants:hash_size()*8,
    HtB = constants:height_bits(),
    TB = constants:time_bits(),
    VB = constants:version_bits(),
    DB = 16,
    <<PrevHash:HB/bitstring,
     Height:HtB,
     Time:TB,
     Version:VB,
     TreesHash:HB/bitstring,
     TxsProofHash:HB/bitstring,
     Difficulty:DB,
     Nonce:HB/bitstring
    >> = H,
    #header{prev_hash = PrevHash,
            height = Height,
            time = Time,
            version = Version,
            trees_hash = TreesHash,
            txs_proof_hash = TxsProofHash,
            difficulty = Difficulty,
            nonce = Nonce}.
difficulty_should_be(NextHeader, A) ->%Next is built on A
    D1 = A#header.difficulty,
    Height = A#header.height,
    {ok, {A, PrevEWAH}} = read_ewah(block:hash(serialize(A))),
    EWAH = calc_ewah(NextHeader, A, PrevEWAH),
    {new_retarget(A, EWAH), EWAH}.
%-define(hashrate_converter, 1024).
-define(hashrate_converter, 1024).
new_retarget(Header, EWAH0) ->
    EWAH = max(EWAH0, 1),
    Diff = Header#header.difficulty,
    Hashes = pow:sci2int(Diff),
    Estimate = max(1, (?hashrate_converter * Hashes) div EWAH),%in seconds/10
    P = constants:block_period(),
    UL = (P * 6 div 4),
    LL = (P * 3 div 4),
    ND = if
	     Estimate > UL -> pow:recalculate(Diff, UL, Estimate);
	     Estimate < LL -> pow:recalculate(Diff, LL, Estimate);
	     true -> Diff
	 end,
    %if estimate is inside our target range, then leave the difficulty unchanged.
    %if estimate is outside of our target range, then adjust difficulty so that we are barely within the target range.
    max(ND, constants:initial_difficulty()).
retarget(Header, 1, L) -> {L, Header};
retarget(Header, N, L) ->
    {ok, PH} = read(Header#header.prev_hash),
    T = PH#header.time,
    retarget(PH, N-1, [T|L]).
median(L) ->
    S = length(L),
    F = fun(A, B) -> A > B end,
    Sorted = lists:sort(F, L),
    lists:nth(S div 2, Sorted).
empty_data() ->
    GB = block:genesis_maker(),
    Header0 = block:block_to_header(GB),
    HH = block:hash(Header0),
    block_hashes:add(HH),
    #s{top = Header0, 
       top_with_block = Header0,
       headers = dict:store(HH,{Header0, 1000000},dict:new())}.
header_size() ->
    HB = constants:hash_size()*8,
    HtB = constants:height_bits(),
    TB = constants:time_bits(),
    VB = constants:version_bits(),
    DB = 16,
    ((HB*4) + HtB + TB + VB + DB).
add_to_top(H, T) ->
    FT = constants:fork_tolerance(),
    B = length(T) < FT,
    if
        B -> [H|T];
        true ->
            {T2, _} = lists:split(FT-1, T),%remove last element so we only remember ?FT at a time.
            [H|T2]
    end.

% HR = HC * sci2int(diff) div DT
% EWAH = (Converter * N / EWAH0)
calc_ewah(Header, PrevHeader, PrevEWAH0) ->
    PrevEWAH = max(1, PrevEWAH0),
    DT = Header#header.time - PrevHeader#header.time,
    %io:fwrite("DT is "),
    %io:fwrite(integer_to_list(DT)),
    %io:fwrite("\n"),
    true = DT > 0,
    true = Header#header.time < (block:time_now() + 20),%give 2 seconds gap in case system time is a little off.
    Hashrate0 = max(1, ?hashrate_converter * pow:sci2int(PrevHeader#header.difficulty) div DT),

    %Hashrate = min(Hashrate0, PrevEWAH * 4),
    %Hashrate = max(Hashrate1, PrevEWAH div 2),

    %N = 20,
    %EWAH = (Hashrate + ((N - 1) * PrevEWAH)) div N,
    
    N = 20,
    Converter = PrevEWAH * 1024000,
    EWAH0 = (Converter div Hashrate0) + ((((N - 1) * Converter) div PrevEWAH)),
    EWAH = (Converter * N div EWAH0),
    %io:fwrite("header number "),
    %io:fwrite(integer_to_list(Header#header.height)),
    %io:fwrite(" prev_ewah: "),
    %io:fwrite(integer_to_list(PrevEWAH)),
    %io:fwrite(" dt: "),
    %io:fwrite(integer_to_list(DT)),
    %io:fwrite(" hashrate0: "),
    %io:fwrite(integer_to_list(Hashrate0)),
    %io:fwrite(" ewah0: "),
    %io:fwrite(integer_to_list(EWAH0)),
    %io:fwrite(" ewah: "),
    %io:fwrite(integer_to_list(EWAH)),
    %io:fwrite("\n"),



    %Height = Header#header.height,
    Diff = Header#header.difficulty,
    if
	Diff == undefined -> ok;
	false -> 
	    Hashes = pow:sci2int(Diff),
	    Estimate = max(1, (?hashrate_converter * Hashes) div EWAH),%in seconds/10
	    io:fwrite(integer_to_list(Header#header.height)),
	    io:fwrite(" EWAH estimate: "),
	    io:fwrite(integer_to_list(Estimate)),
	    io:fwrite(" time: "),
	    io:fwrite(integer_to_list(DT)),
	    io:fwrite(" \n"),
	    ok;
	true -> ok
    end,

    %io:fwrite(packer:pack([PrevEWAH0, DT, EWAH])),
    %io:fwrite("ewah "),
    %io:fwrite(integer_to_list(Hashrate)),
    %io:fwrite(" "),
    %io:fwrite(integer_to_list(EWAH)),
    %io:fwrite("\n"),
    %io:fwrite("\n"),
    EWAH.
    
%EWAH = (Converter div ((Converter div Hashrate) + (((N - 1) * (Converter div PrevEWAH))))) div N.
    %EWAH0 = (Hashrate + ((N - 1) * PrevEWAH)) div N.
%average 1 6 9 -> 16/3
%average 1/1 1/6 1/9 -> 23/18/3 ~ -> 4/9
ewah_range(Start, End) ->
    EH = block:hash(block:get_by_height(End)),
    ewah_range2(EH, Start, []).
ewah_range2(EH, Start, X) ->
    {ok, {Header, EWAH}} = read_ewah(EH),
    Height = Header#header.height,
    if
	Height < Start -> X;
	true -> 
	    ewah_range2(Header#header.prev_hash,
			Start,
			[EWAH|X])
    end.
	    
    

test() ->
    H = hash:doit(<<>>),
    Header1 = make_header(H, 0, 0, 0, H, H, 0, 0),
    absorb([Header1]),
    H1 = block:hash(serialize(Header1)),
    {ok, Header1} = read(H1),
    success.
    
test2() ->
    H = hash:doit(<<>>),
    Header = setelement(10, make_header(H, 0, 0, 0, H, H, 0, 0), undefined),
    Header = deserialize(serialize(Header)),
    absorb([Header]),
    H1 = block:hash(serialize(Header)),
    Header2 = setelement(10, make_header(H1, 0, 0, 0, H, H, 0, 0), undefined),
    absorb([Header2]),
    H1 = block:hash(Header),
    {ok, Header} = read(H1),
    success.
