-module(test_txs).
-export([test/0, test/1, mine_blocks/1, absorb/1]).
 
-include("../records.hrl").
test() ->
    unlocked = keys:status(),
    Pub = constants:master_pub(),
    Pub = keys:pubkey(),

    S = success,
    S = test(1),%create account, spend, delete %S = test(2),%repo tx
    S.
absorb(Tx) -> 
    %tx_pool_feeder:absorb_unsafe(Tx).
    tx_pool_feeder:absorb(Tx).
    %timer:sleep(400).
block_trees(X) ->
    X#block.trees.
test(1) ->
    io:fwrite(" create_account tx test \n"),
    %create account, spend, delete account
    headers:dump(),
    block:initialize_chain(),
    tx_pool:dump(),
    %BP = block:get_by_height_in_chain(0, headers:top()),
    BP = block:get_by_height(0),
    PH = block:hash(BP),
    Trees = block_trees(BP),
    {NewPub,NewPriv} = testnet_sign:new_key(),

    Fee = constants:initial_fee() + 20,
    {Ctx, _} = create_account_tx:new(NewPub, 100000000, Fee, constants:master_pub(), Trees),
    Stx = keys:sign(Ctx),
    absorb(Stx),
    Ctx2 = spend_tx:make_dict(NewPub, 10, Fee, constants:master_pub()),
    Stx2 = keys:sign(Ctx2),
    absorb(Stx2),
    Ctx21 = spend_tx:make_dict(NewPub, 10, Fee, constants:master_pub()),
    Stx21 = keys:sign(Ctx21),
    absorb(Stx21),
    timer:sleep(20),
    Ctx3 = delete_account_tx:make_dict(constants:master_pub(), NewPub, Fee),
    Stx3 = testnet_sign:sign_tx(Ctx3, NewPub, NewPriv),
    absorb(Stx3),
    Ctx4 = create_account_tx:make_dict(NewPub, 100000000, Fee, constants:master_pub()),
    Stx4 = keys:sign(Ctx4),
    absorb(Stx4),
    potential_block:new(),

    Txs = (tx_pool:get())#tx_pool.txs,
    mine_blocks(1),

    success;
test(17) ->
    test({17, 1});
test({17, N}) ->
    io:fwrite(packer:pack(now())),
    io:fwrite("\n"),
    %fill blocks completely with create_account txs.
    create_accounts(636, N),%fits 636 at the start.
    io:fwrite(packer:pack(now())),
    io:fwrite("\n"),
    %mine_blocks(1),
    potential_block:new(),
    block:mine(100000),
    io:fwrite(packer:pack(now())),
    io:fwrite("\n"),
    timer:sleep(300),
    success;
test(18) ->
    test18(10000);
test(19) ->
    {NewPub,_NewPriv} = testnet_sign:new_key(<<10000:256>>),
    Fee = constants:initial_fee() + 20,
    Ctx = create_account_tx:make_dict(NewPub, 1, Fee, constants:master_pub()),
    Stx = keys:sign(Ctx),
    absorb(Stx),
    timer:sleep(2000),
    potential_block:new(),
    block:mine(100000),
    block:mine(100000),
    timer:sleep(300),
    PerBlock = 650,
    %PerBlock = 10,
    %PerBlock = 1,
    Rounds = 20,
    spend_lots(Rounds, PerBlock, PerBlock, NewPub).
    
    
test18(0) -> success;
test18(N) ->
    test({17, N}),
    test18(N-1).
spend_lots(0, _, _, _) -> ok;
spend_lots(N, 0, M, P) -> 
    potential_block:new(),
    block:mine(100000),
    timer:sleep(300),
    spend_lots(N-1, M, M, P);
spend_lots(N, M, L, P) ->
    io:fwrite("spend "),
    io:fwrite(integer_to_list(M)),
    io:fwrite("\n"),
    Fee = constants:initial_fee() + 20,
    Ctx = spend_tx:make_dict(P, 1, Fee, constants:master_pub()),
    Stx = keys:sign(Ctx),
    absorb(Stx),
    %timer:sleep(30),
    spend_lots(N, M-1, L, P).
create_accounts(0, Salt) -> ok;
create_accounts(N, Salt) ->
    io:fwrite("create account "),
    io:fwrite(integer_to_list(N)),
    io:fwrite("\n"),
    M = N + (1000*Salt),
    {NewPub,_NewPriv} = testnet_sign:new_key(<<M:256>>),
    Fee = constants:initial_fee() + 20,
    Ctx = create_account_tx:make_dict(NewPub, 1, Fee, constants:master_pub()),
    Stx = keys:sign(Ctx),
    absorb(Stx),
    create_accounts(N-1, Salt).
slash_exists([]) -> false;
slash_exists([Tx|T]) ->
    is_slash(Tx) or slash_exists(T).
is_slash(STx) ->
    Tx = testnet_sign:data(STx),
    channel_slash_tx:is_tx(Tx).
	     
mine_blocks(Many) when Many < 1 -> ok;
mine_blocks(Many) ->
    %only works if you set the difficulty very low.
    TP = tx_pool:get(),
    Txs = TP#tx_pool.txs,
    Height = TP#tx_pool.height,
    PB = block:get_by_height(Height),
    Hash = block:hash(PB),
    {ok, Top} = headers:read(Hash),
    Block = block:make(Top, Txs, block_trees(PB), keys:pubkey()),
    block:mine(Block, 10),
    timer:sleep(1000),
    mine_blocks(Many-1).
