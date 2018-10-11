-module(headers).
-behaviour(gen_server).
-export([absorb/1, absorb_with_block/1, read/1, read_ewah/1, top/0, dump/0, top_with_block/0,
         make_header/9, serialize/1, deserialize/1,
         difficulty_should_be/2, 
	 ewah_range/2,
	 test/0]).
-export([start_link/0,init/1,handle_call/3,handle_cast/2,handle_info/2,terminate/2,code_change/3]).
-include("../../records.hrl").
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
				error -> io:fwrite("don't have a parent for this header\n"),
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
					_ -> 
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
    F2 = forks:get(2),
    Height = Header#header.height,
    Fork = if
	       F2 > Height -> 0;
	       true -> 1
	   end,
    pow:check_pow({pow, Data, MineDiff, Nonce}, constants:hash_size(), Fork).

check_difficulty(A) ->
    {B, EWAH} = case A#header.height < 2 of
            true ->
                %{constants:initial_difficulty(), A#header.period};
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
make_header(PH, 0, Time, Version, TreesHash, TxsProofHash, Nonce, Difficulty, Period) ->
    #header{prev_hash = PH,
	    height = 0, 
	    time = Time, 
	    version = Version,
	    trees_hash = TreesHash,
	    txs_proof_hash = TxsProofHash,
	    nonce = <<Nonce:256>>,
	    difficulty = Difficulty,
	    accumulative_difficulty = 0,
            period = Period};
make_header(PH, Height, Time, Version, Trees, TxsProodHash, Nonce, Difficulty, Period) ->
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
            accumulative_difficulty = AC,
            period = Period}.
serialize(H) ->
    false = H#header.prev_hash == undefined,
    HtB = constants:height_bits(),
    TB = constants:time_bits(),
    VB = constants:version_bits(),
    DB = 16,
    PB = constants:period_bits(),
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
     (H#header.nonce)/binary,
     (H#header.period):PB
    >>.
deserialize(H) ->
    HB = constants:hash_size()*8,
    HtB = constants:height_bits(),
    TB = constants:time_bits(),
    VB = constants:version_bits(),
    PB = constants:period_bits(),
    DB = 16,
    <<PrevHash:HB/bitstring,
     Height:HtB,
     Time:TB,
     Version:VB,
     TreesHash:HB/bitstring,
     TxsProofHash:HB/bitstring,
     Difficulty:DB,
     Nonce:HB/bitstring,
     Period:PB
    >> = H,
    #header{prev_hash = PrevHash,
            height = Height,
            time = Time,
            version = Version,
            trees_hash = TreesHash,
            txs_proof_hash = TxsProofHash,
            difficulty = Difficulty,
            period = Period,
            nonce = Nonce}.
difficulty_should_be(NextHeader, A) ->%Next is built on A
    D1 = A#header.difficulty,
    RF = constants:retarget_frequency(),
    Height = A#header.height,
    %X = Height rem RF,%fork
    B = Height > forks:get(4),
    X = if
	    B -> Height rem (RF div 2);
	    true -> Height rem RF
	end,
    {ok, {A, PrevEWAH}} = read_ewah(hash:doit(serialize(A))),
    EWAH = calc_ewah(NextHeader, A, PrevEWAH),
    B2 = Height > forks:get(7),
    if
	B2 -> 
	    %io:fwrite("prevewah is "),
	    %io:fwrite(integer_to_list(PrevEWAH)),
	    %io:fwrite("\n"),
	    %io:fwrite("ewah is "),
	    %io:fwrite(integer_to_list(EWAH)),
	    %io:fwrite("\n"),
	    {new_retarget(A, EWAH), EWAH};
        (X == 0) and (not(Height < 10)) ->
            %{difficulty_should_be2(A), A#header.period};
            {difficulty_should_be2(A), EWAH};
        true ->
            %{D1, A#header.period}
            {D1, EWAH}
    end.
%-define(hashrate_converter, 1024).
-define(hashrate_converter, 1024).
new_retarget(Header, EWAH0) ->
    EWAH = max(EWAH0, 1),
    Diff = Header#header.difficulty,
    Hashes = pow:sci2int(Diff),
    Estimate = max(1, (?hashrate_converter * Hashes) div EWAH),%in seconds/10
    %io:fwrite("period is "),
    %io:fwrite(integer_to_list(P)),
    %io:fwrite("\n"),
    %io:fwrite("diff is "),
    %io:fwrite(integer_to_list(Diff)),
    %io:fwrite("\n"),
    %io:fwrite("ewah is "),
    %io:fwrite(integer_to_list(EWAH)),
    %io:fwrite("\n"),
    %io:fwrite("ewah is "),
    %io:fwrite(integer_to_list(EWAH)),
    %io:fwrite("\n"),
    P = Header#header.period,
    UL = (P * 6 div 4),
    LL = (P * 3 div 4),
    %io:fwrite("estimate is "),
    %io:fwrite(integer_to_list(LL)),
    %io:fwrite(" "),
    %io:fwrite(integer_to_list(Estimate)),
    %io:fwrite(" "),
    %io:fwrite(integer_to_list(UL)),
    %io:fwrite("\n"),

    %io:fwrite("\n"),
    %UL = (P * 2) * TT,
    %LL = P * TT,
    ND = if
	     Estimate > UL -> pow:recalculate(Diff, UL, Estimate);
	     Estimate < LL -> pow:recalculate(Diff, LL, Estimate);
	     true -> Diff
	 end,
    %Estimate = Use EWAH and Diff to estimate the current period
    %if estimate is inside our target range, then leave the difficulty unchanged.
    %if estimate is outside of our target range, then adjust difficulty so that we are barely within the target range.
    max(ND, constants:initial_difficulty()).
difficulty_should_be2(Header) ->
    F = constants:retarget_frequency() div 2,
    {Times1, Hash2000} = retarget(Header, F, []),
    {Times2, _} = retarget(Hash2000, F, []),
    M1 = median(Times1),
    M2 = median(Times2),
    Tbig = M1 - M2,
    T0 = Tbig div F,%T is the estimated block time over last 2000 blocks.
    T1 = max(1, T0),
    T = min(T1, Header#header.period * 7 div 6),
    NT = pow:recalculate(Hash2000#header.difficulty,
                         Header#header.period,
                         T),
    max(NT, constants:initial_difficulty()).
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
       %headers = dict:store(HH,{Header0, Header0#header.period},dict:new())}.
       headers = dict:store(HH,{Header0, 1000000},dict:new())}.
header_size() ->
    HB = constants:hash_size()*8,
    HtB = constants:height_bits(),
    TB = constants:time_bits(),
    VB = constants:version_bits(),
    DB = 16,
    ((HB*4) + HtB + TB + VB + DB).
add_to_top(H, T) ->
    {ok, FT} = application:get_env(amoveo_core, fork_tolerance),
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
    Header1 = make_header(H, 0, 0, 0, H, H, 0, 0, 0),
    absorb([Header1]),
    H1 = hash:doit(serialize(Header1)),
    {ok, Header1} = read(H1),
    success.
    
test2() ->
    H = hash:doit(<<>>),
    Header = setelement(10, make_header(H, 0, 0, 0, H, H, 0, 0, 0), undefined),
    Header = deserialize(serialize(Header)),
    absorb([Header]),
    H1 = hash:doit(serialize(Header)),
    Header2 = setelement(10, make_header(H1, 0, 0, 0, H, H, 0, 0, 0), undefined),
    absorb([Header2]),
    H1 = block:hash(Header),
    {ok, Header} = read(H1),
    success.
