-module(block).
-export([block_to_header/1, get_by_height_in_chain/2,
         get_by_height/1, hash/1, get_by_hash/1, 
         initialize_chain/0, make/4,
         mine/1, mine/2, mine2/2, check/1, check0/1,
         top/0, genesis_maker/0, height/0,
	 time_now/0, all_mined_by/1, time_mining/1,
	 period_estimate/0, hashrate_estimate/0,
	 period_estimate/1, hashrate_estimate/1,
	 hashes_per_block/0, hashes_per_block/1,
         test/0]).
%Read about why there are so many proofs in each block in docs/design/light_nodes.md
-include("../records.hrl").
-record(roots, {accounts}).

tx_hash(T) -> hash:doit(T).
proof_hash(P) -> hash:doit(P).
merkelize_thing(X) when is_binary(X) -> X;
merkelize_thing(X) when is_tuple(X) and (size(X) > 0)->
    T = element(1, X),
    case T of
        proof -> proof_hash(X);
        _ -> tx_hash(X)
    end;
merkelize_thing(X) -> hash:doit(X).
    
merkelize_pair(A, B) ->
    C = [merkelize_thing(A), merkelize_thing(B)],
    hash:doit(C).
merkelize([A]) -> merkelize_thing(A);
merkelize([A|[B|T]]) ->
    merkelize(merkelize2([A|[B|T]]));
merkelize([]) -> <<0:256>>.
merkelize2([]) -> [];
merkelize2([A]) -> [merkelize_thing(A)];
merkelize2([A|[B|T]]) ->
    [merkelize_pair(A, B)|
     merkelize2(T)].
    
txs_proofs_hash(Txs, Proofs) ->
    TB = merkelize(Txs),
    PB = merkelize(Proofs),
    X = <<TB/binary, PB/binary>>,
    hash:doit(X).
block_to_header(B) ->
    %io:fwrite("block to header "),
    %io:fwrite(integer_to_list(B#block.height)),
    %io:fwrite("\n"),
    BV = [{1, B#block.market_cap}],
    StateRoot = merkelize(BV ++ B#block.txs ++ B#block.proofs),
    headers:make_header(
      B#block.prev_hash,
      B#block.height,
      B#block.time,
      B#block.version,
      B#block.trees_hash,
      StateRoot,
      B#block.nonce,
      B#block.difficulty).

hash(error) -> 1=2;
hash(B) when is_binary(B) ->%accepts binary headers
    case size(B) == constants:hash_size() of
        true ->
            B;
        false ->
            hash:doit(hash:doit(B))
    end;
hash(B) when element(1, B) == header ->
    hash(headers:serialize(B));
hash(B) when is_record(B, block) ->
    hash(block_to_header(B)).

calculate_prev_hashes(Parent) ->
    H = Parent#header.height,
    PH = hash(Parent),
    calculate_prev_hashes([PH], H, 2).

calculate_prev_hashes([PH|Hashes], Height, N) ->
    NHeight = Height - N,
    case NHeight < 1 of
        true ->
            list_to_tuple([prev_hashes|lists:reverse([PH|Hashes])]);
        false ->
            B = get_by_height_in_chain(NHeight, PH),
            calculate_prev_hashes([hash(B)|[PH|Hashes]], NHeight, N*2)
    end.
get_by_hash(H) ->
    Hash = hash(H),
    BlockFile = utils:binary_to_file_path(blocks, Hash),
    case db:read(BlockFile) of
        [] -> empty;
        Block -> binary_to_term(zlib:uncompress(Block))
    end.
top() -> top(headers:top_with_block()).%what we actually want is the highest header for which we have a stored block.
top(Header) ->
    false = element(2, Header) == undefined,
    case get_by_hash(hash(Header)) of
        empty -> 
            {ok, PrevHeader} = 
                headers:read(Header#header.prev_hash),
            top(PrevHeader);
        Block -> Block
    end.
%height() -> (top())#block.height.
height() ->
    TH = headers:top_with_block(),
    TH#header.height.
lg(X) when (is_integer(X) and (X > 0)) ->
    lgh(X, 0).
lgh(1, X) -> X;
lgh(N, X) -> lgh(N div 2, X+1).
get_by_height(N) ->
    get_by_height_in_chain(N, headers:top_with_block()).
get_by_height_in_chain(N, BH) when N > -1 ->
    Block = get_by_hash(hash(BH)),
    case Block of
        empty ->
            PrevHash = BH#header.prev_hash,
            {ok, PrevHeader} = headers:read(PrevHash),
            get_by_height_in_chain(N, PrevHeader);
        _  ->
            M = Block#block.height,
            D = M - N,
            if
                D < 0 -> empty;
                D == 0 -> Block;
                true ->
                    PrevHash = prev_hash(lg(D), Block),
                    {ok, PrevHeader} = headers:read(PrevHash),
                    get_by_height_in_chain(N, PrevHeader)
            end
    end.
prev_hash(0, BP) -> BP#block.prev_hash;
prev_hash(N, BP) -> element(N+1, BP#block.prev_hashes).
time_now() ->
    (os:system_time() div (1000000 * constants:time_units())) - constants:start_time().
genesis_maker() ->
    Root0 = constants:root0(),
    %Pub = constants:master_pub(),
    %First = accounts:new(Pub, constants:initial_coins()),
    %GovInit = governance:genesis_state(),
    %Accounts = accounts:write(First, Root0),%This is leaking a small amount of memory, but it is probably too small to care about, since this function gets executed so rarely.
    Accounts = Root0,
    Trees = trees:new(Accounts),
    TreesRoot = trees:root_hash(Trees),
    HistoryString = <<"bitcoin 511599  0000000000000000005cdf7dafbfa2100611f14908ad99098c2a91719da93a50">>,
    Hash = hash:doit(HistoryString),
    #block{height = 0,
           prev_hash = Hash,%<<0:(constants:hash_size()*8)>>,
           txs = [],
           trees_hash = TreesRoot,
           time = 0,
           difficulty = constants:initial_difficulty(),
           version = version:doit(0),
           trees = Trees,
           roots = make_roots(Trees)
          }.
miner_fees([]) -> 0;
miner_fees([H|T]) ->
    element(4, testnet_sign:data(H)) + miner_fees(T).
   
new_dict(Txs, Dict, Height) ->
    txs:digest_from_dict(Txs, Dict, Height).
market_cap(OldBlock, BlockReward, Txs0, Dict, Height) ->
    %DeveloperReward = constants:developer_reward(),
    OldBlock#block.market_cap + BlockReward - 
	burn_fees(Txs0).% + DeveloperReward.
make(Header, Txs0, Trees, Pub) ->
    {CB, _Proofs} = coinbase_tx:make(Pub, Trees),
    Txs = [CB|lists:reverse(Txs0)],
    Height = Header#header.height,
    Querys = proofs:txs_to_querys(Txs, Trees, Height+1),
    Facts = proofs:prove(Querys, Trees),
    Dict = proofs:facts_to_dict(Facts, dict:new()),
    NewDict = new_dict(Txs, Dict, Height + 1),
    MinerAddress = Pub,
    MinerReward = miner_fees(Txs0),
    MinerAccount = accounts:dict_update(MinerAddress, NewDict, MinerReward, none),
    NewDict2 = accounts:dict_write(MinerAccount, NewDict),
    NewTrees = tree_data:dict_update_trie(Trees, NewDict2),
    %Governance = trees:governance(NewTrees),
    %Governance = trees:governance(Trees),
    BlockPeriod = constants:block_period(),
    PrevHash = hash(Header),
    OldBlock = get_by_hash(PrevHash),
    BlockReward = constants:block_reward(),
    MarketCap = market_cap(OldBlock, BlockReward, Txs0, Dict, Height),
    TimeStamp = time_now(),
    NextHeader = #header{height = Height + 1, prev_hash = PrevHash, time = TimeStamp},
    Block = #block{height = Height + 1,
		   prev_hash = hash(Header),
		   txs = Txs,
		   trees_hash = trees:root_hash(NewTrees),
		   time = TimeStamp,
		   difficulty = element(1, headers:difficulty_should_be(NextHeader, Header)),
		   version = version:doit(Height+1),%constants:version(),
		   trees = NewTrees,
		   prev_hashes = calculate_prev_hashes(Header),
		   proofs = Facts,
                   roots = make_roots(Trees),
		   %market_cap = OldBlock#block.market_cap + BlockReward - burn_fees(Txs0, Governance),
		   market_cap = MarketCap
		  },
    Block = packer:unpack(packer:pack(Block)),
    %_Dict = proofs:facts_to_dict(Proofs, dict:new()),
    Block.
make_roots(Trees) ->
    #roots{accounts = trie:root_hash(accounts, Trees)}.
roots_hash(X) when is_record(X, roots) ->
    A = X#roots.accounts,
    hash:doit(<<A/binary>>).
    
guess_number_of_cpu_cores() ->
    case application:get_env(amoveo_core, test_mode) of
        {ok, true} -> 1;
        {ok, false} ->
            X = erlang:system_info(logical_processors_available),
            Y = if
                    X == unknown ->
                        % Happens on Mac OS X.
                        erlang:system_info(schedulers);
                    is_integer(X) -> 
                        %ubuntu
                        X;
                    true -> io:fwrite("number of CPU unknown, only using 1"), 1
                end,
            {ok, CoresToMine} = application:get_env(amoveo_core, cores_to_mine),
            min(Y, CoresToMine)
    end.
spawn_many(0, _) -> ok;
spawn_many(N, F) -> 
    spawn(F),
    spawn_many(N-1, F).
mine(Rounds) -> 
    potential_block:save(),
    Block = potential_block:read(),
    case Block of
	"" ->
	    io:fwrite("potential block empty\n"),
	    timer:sleep(100),
	    mine(Rounds);
	_ ->
	    mine(Block, Rounds)
    end.
    %Block = potential_block:check(),
mine(Block, Rounds) ->
    %Cores = guess_number_of_cpu_cores(),
    Cores = 1, %slow down mining so I don't break the computer.
    mine(Block, Rounds, Cores).
mine(Block, Rounds, Cores) ->
    F = fun() ->
                case mine2(Block, Rounds) of
                    false -> false;
                    PBlock ->
                        io:fwrite("found a block\n"),
                        Header = block_to_header(PBlock),
                        headers:absorb([Header]),
			headers:absorb_with_block([Header]),
                        block_organizer:add([PBlock])
                end
        end,
    spawn_many(Cores-1, F),
    F().
mine2(Block, Times) ->
    PH = Block#block.prev_hash,
    ParentPlus = get_by_hash(PH),
    Trees = ParentPlus#block.trees,
    MineDiff = Block#block.difficulty,
    case pow:pow(hash(Block), MineDiff, Times, 1) of
        false -> false;
        Pow -> Block#block{nonce = pow:nonce(Pow)}
    end.
proofs_roots_match([], _) -> true;
proofs_roots_match([P|T], R) ->
    Tree = proofs:tree(P),
    Root = proofs:root(P),
    Tree = accounts,
    Root = R#roots.accounts,
    proofs_roots_match(T, R).
            
check0(Block) ->%This verifies the txs in ram. is parallelizable
    Facts = Block#block.proofs,
    Header = block_to_header(Block),
    BlockHash = hash(Block),
    {ok, Header} = headers:read(BlockHash),
    Roots = Block#block.roots,
    PrevStateHash = roots_hash(Roots),
    {ok, PrevHeader} = headers:read(Block#block.prev_hash),
    %io:fwrite([Roots, PrevStateHash, PrevHeader#header.trees_hash]),
    PrevStateHash = PrevHeader#header.trees_hash,
    Txs = Block#block.txs,
    true = proofs_roots_match(Facts, Roots),
    Dict = proofs:facts_to_dict(Facts, dict:new()),
    Height = Block#block.height,
    PrevHash = Block#block.prev_hash,
    Pub = coinbase_tx:from(hd(Block#block.txs)),
    true = no_coinbase(tl(Block#block.txs)),
    NewDict = new_dict(Txs, Dict, Height),
    {Dict, NewDict, BlockHash}.


check(Block) ->%This writes the result onto the hard drive database. This is non parallelizable.
    Roots = Block#block.roots,
    {Dict, NewDict, BlockHash} = Block#block.trees,
    {ok, Header} = headers:read(BlockHash),
    Height = Block#block.height,
    OldBlock = get_by_hash(Block#block.prev_hash),
    OldTrees = OldBlock#block.trees,
    Txs = Block#block.txs,
    Txs0 = tl(Txs),
    BlockSize = size(packer:pack(Txs)),
    MaxBlockSize = constants:max_block_size(),
    ok = case BlockSize > MaxBlockSize of
	     true -> 
		 io:fwrite("error, this block is too big\n"),
		 bad;
	     false -> ok
    end,
    BlockReward = constants:block_reward(),
    MarketCap = market_cap(OldBlock, BlockReward, Txs0, Dict, Height-1),
    true = Block#block.market_cap == MarketCap,
    MinerAddress = element(2, hd(Txs)),
    MinerReward = miner_fees(Txs0),
    MinerAccount = accounts:dict_update(MinerAddress, NewDict, MinerReward, none),
    NewDict3 = accounts:dict_write(MinerAccount, NewDict),
    NewTrees3 = tree_data:dict_update_trie(OldTrees, NewDict3),
    Block2 = Block#block{trees = NewTrees3},
    TreesHash = Block2#block.trees_hash,
    %TreesHash = trees:root_hash2(NewTrees3, Roots),
    %TreesHash = trees:root_hash(Roots#roots.accounts),
    %TreesHash = hash:doit(trie:root_hash(accounts, Roots#roots.accounts)),
    TreesHash = hash:doit(trie:root_hash(accounts, NewTrees3)),
    {true, Block2}.

no_coinbase([]) -> true;
no_coinbase([STx|T]) ->
    Tx = testnet_sign:data(STx),
    Type = element(1, Tx),
    false = Type == coinbase,
    no_coinbase(T).

initialize_chain() -> 
    %only run genesis maker once, or else it corrupts the database.
    {ok, L} = file:list_dir("data/blocks"),
    %B = length(L) < 1,
    B = true,
    GB = if
        B -> G = genesis_maker(),
             block_absorber:do_save(G),
             G;
        true -> get_by_height(0)
         end,
    Header0 = block_to_header(GB),
    block_hashes:add(block:hash(Header0)),
    gen_server:call(headers, {add, block:hash(Header0), Header0, 1}),
    gen_server:call(headers, {add_with_block, block:hash(Header0), Header0}),
    Header0.

burn_fees([]) -> 0;
burn_fees([Tx|T]) ->
    C = testnet_sign:data(Tx),
    Type = element(1, C),
    A = constants:tx_fee(),
    A + burn_fees(T).
all_mined_by(Address) ->
    B = top(),
    Height = B#block.height,
    bmb_helper(Address, [], hash(B), Height - 1).
bmb_helper(Address, Out, Hash, 0) -> Out;
bmb_helper(Address, Out, Hash, Height) ->
    B = block:get_by_hash(Hash),
    Txs = B#block.txs,
    CB = hd(Txs),
    A2 = element(2, CB),
    Out2 = if
	       Address == A2 -> [Height|Out];
	       true -> Out
	   end,
    PH = B#block.prev_hash,
    bmb_helper(Address, Out2, PH, Height - 1).
time_mining(X) -> time_mining(0, X, []).
time_mining(S, [], X) -> tl(lists:reverse(X));
time_mining(S, Heights, Outs) ->
    B = block:get_by_height(hd(Heights)),
    T = B#block.time,
    T2 = T - S,
    time_mining(T, tl(Heights), [(T-S)|Outs]).

period_estimate() ->
    period_estimate(top()).
period_estimate(T) when is_integer(T) ->
    period_estimate(get_by_height(T));
period_estimate(T) ->
    %estimates seconds per block
    H = T#block.height,
    true = H > 21,
    X = get_by_height(H-20),
    Time1 = X#block.time,
    Time2 = T#block.time,
    (Time2 - Time1) div 200.
hashes_per_block() ->
    hashes_per_block(top()).
hashes_per_block(B) ->
    D = B#block.difficulty,
    diff2hashes(D) div 1000000000.
hashrate_estimate() ->
    hashrate_estimate(top()).
hashrate_estimate(T) when is_integer(T) ->
    hashrate_estimate(get_by_height(T));
hashrate_estimate(T) ->
    %estimates hashes per second
    D = T#block.difficulty,
    Hashes = diff2hashes(D),
    X = Hashes / period_estimate(T) / 1000000000,
    %io:fwrite("in gigahashes per second "),
    %io:fwrite(integer_to_list(round(10*X))),
    %io:fwrite("\n"),
    round(X).
diff2hashes(D) ->
    A = D div 256,
    B = D rem 256,
    exponent(2, A) * (256 + B) div 256.
exponent(_, 0) -> 1;
exponent(A, 1) -> A;
exponent(A, N) when N rem 2 == 0 -> 
    exponent(A*A, N div 2);
exponent(A, N) -> 
    A*exponent(A, N-1).
	    
test() ->
    test(1).
test(1) ->
    Header0 = headers:top(),
    Block0 = get_by_hash(Header0),
    Trees = Block0#block.trees,
    make_roots(Trees),
    Pub = keys:pubkey(),
    Block1 = make(Header0, [], Trees, Pub),
    WBlock10 = mine2(Block1, 10),
    Header1 = block_to_header(WBlock10),
    headers:absorb([Header1]),
    headers:absorb_with_block([Header1]),
    H1 = hash(Header1),
    H1 = hash(WBlock10),
    {ok, Header1} = headers:read(H1),
    block_organizer:add([WBlock10]),
    timer:sleep(200),
    WBlock11 = get_by_hash(H1),
    WBlock11 = get_by_height_in_chain(1, H1),
    %io:fwrite(packer:pack(WBlock11)),
    %io:fwrite("\n"),
    %io:fwrite(packer:pack(WBlock10)),
    %io:fwrite("\n"),
    WBlock10 = WBlock11#block{trees = WBlock10#block.trees},
    success;
test(2) ->
    {_, _, Proofs} = accounts:get(keys:pubkey(), 1),
    _Proof = hd(Proofs).
