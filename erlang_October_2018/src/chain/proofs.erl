-module(proofs).
-export([prove/2, test/0, hash/1, facts_to_dict/2, txs_to_querys/3, 
         root/1, tree/1, path/1, value/1,
         key/1]).
-define(Header, 1).
-include("../records.hrl").
-record(proof, {tree, value, root, key, path}).

root(X) -> X#proof.root.
key(X) -> X#proof.key.
value(X) -> X#proof.value.
path(X) -> X#proof.path.
tree(X) -> int_to_tree(X#proof.tree).

%we use a deterministic merge sort that removes repeats while sorting.
tree_to_int(accounts) -> 1.

int_to_tree(1) -> accounts.

%deterministic merge-sort    
compare({Ta, Ka}, {Tb, Kb}) ->
    T0 = tree_to_int(Ta),
    T1 = tree_to_int(Tb),
    if
        T0 < T1 -> true;
	T0 > T1 -> false;
	Ka < Kb -> true;
	Ka > Kb -> false;
	true -> repeat
    end.
merge([], []) -> [];
merge([], T) -> T;
merge(T, []) -> T;
merge([A|B], [S|T]) ->
    C = compare(A, S),
    case C of
	repeat -> [A|merge(B, T)];
	true -> [A|merge(B, [S|T])];
	false -> [S|merge([A|B], T)]
    end.
det_improve([]) -> [];
det_improve([A]) -> [A];
det_improve([A|[B|T]]) ->
    [merge(A, B)|det_improve(T)].
det_helper([]) -> [];
det_helper([A]) -> A;
det_helper(L) ->
    det_helper(det_improve(L)).
to_lists([]) -> [];
to_lists([A|T]) -> [[A]|to_lists(T)].
det_order(Querys) ->    
    F = to_lists(Querys),
    det_helper(F).
%finished defining merge-sort.       

prove(Querys, Trees) ->
    F2 = det_order(Querys),
    prove2(F2, Trees).
prove2([], _) ->
    [];
prove2([{Tree, Key}|T], Trees) ->
    %Branch = trees:Tree(Trees),
    Tree = accounts,
    Branch = Trees,
    {Root, Data, Path} = Tree:get(Key, Branch),
    Data2 = case Data of
		empty -> 0;
		_ -> Tree:serialize(Data)
	    end,
    Proof = #proof{root = Root,
		  key = Key,
		  path = Path, 
		  value = Data2,
		  tree = tree_to_int(Tree)},
    true = Tree:verify_proof(Root, Key, Data2, Path),
    [Proof|prove2(T, Trees)].
facts_to_dict([], D) -> D;
facts_to_dict([F|T], D) ->
    Tree = int_to_tree(F#proof.tree),
    Key2 = F#proof.key,
    true = 
        Tree:verify_proof(
          F#proof.root,
          Key2,
          F#proof.value,
          F#proof.path),
    Key = F#proof.key,
    Value0 = F#proof.value,
    D2 = dict:store({Tree, Key}, Value0, D),
    facts_to_dict(T, D2).
hash(F) ->
    hash:doit(F).
governance_to_querys(Gov) ->
    Leaves = trie:get_all(Gov, governance),
    Keys = leaves_to_querys(Leaves).
leaves_to_querys([]) -> [];
leaves_to_querys([L|T]) ->
    Q = {governance, leaf:key(L)},
    [Q|leaves_to_querys(T)].
txs_to_querys([C|T], Trees, Height) -> 
    case element(1, C) of
        coinbase ->
            [
             {accounts, coinbase_tx:from(C)}
            ] ++
                txs_to_querys2(T, Trees, Height);
        signed -> txs_to_querys2([C|T], Trees, Height)
    end.
txs_to_querys2([], _, _) -> [];
txs_to_querys2([STx|T], Trees, Height) ->
    Tx = STx#signed.data,
    %Tx = testnet_sign:data(STx),
    PS = constants:pubkey_size() * 8,
    Spend = element(1, Tx),
    Spend = spend,
    [
     {accounts, spend_tx:from(Tx)},
     {accounts, spend_tx:to(Tx)}
    ]
	++ txs_to_querys2(T, Trees, Height).
test() ->
    headers:dump(),
    %block:initialize_chain(),
    tx_pool:dump(),
    test_txs:mine_blocks(2),
    timer:sleep(150),
    Question = <<>>,
    OID = <<2:256>>,
    Fee = 20 + constants:initial_fee(),
    Tx = oracle_new_tx:make_dict(constants:master_pub(), Fee, Question, 1 + block:height(), OID, 0, 0),
    %{Tx, _} = oracle_new_tx:make(constants:master_pub(), Fee, Question, 1, OID, 0, 0, Trees0),
    tx_pool_feeder:absorb(keys:sign(Tx)),
    test_txs:mine_blocks(1),
    timer:sleep(200),
    Trees = (tx_pool:get())#tx_pool.block_trees,
    Pub2 = <<"BL6uM2W6RVAI341uFO7Ps5mgGp4VKZQsCuLlDkVh5g0O4ZqsDwFEbS9GniFykgDJxYv8bNGJ+/NdrFjKV/gJa6c=">>,
    Pub3 = <<"BIG0bGOtCeH+ik2zxohHNOHyydjzIfi2fhKwFCZ0TFh99y+C8eiwHWwWkFrfGtEL7HcKP+5jdQmRc6wfnG32wlc=">>,
    {Pub55, _} = sign2:new_key(),
    PS = constants:pubkey_size() * 8,
    Querys = [{accounts, keys:pubkey()},
	      {accounts, keys:pubkey()},%repeats are ignored
	      {accounts, base64:decode(Pub2)},%empty account
              {accounts, Pub55},
              {accounts, Pub3},
              {accounts, <<297:520>>},
              {accounts, <<744:520>>},
	      {governance, block_reward},
	      {governance, 1},
	      {channels, <<1:256>>},
	      {existence, hash:doit(1)},
	      {oracles, OID},
	      {oracles, <<1:256>>},
	      {orders, #key{pub = keys:pubkey(), id = OID}},
              {oracle_bets, #key{pub = keys:pubkey(), id = OID}}
	     ],% ++
        %governance_to_querys(trees:governance(Trees)),
    Facts = prove(Querys, Trees),
    ProofRoot = hash(Facts),
    Dict = facts_to_dict(Facts, dict:new()), %when processing txs, we use this dictionary to look up the state.
    Querys2 = dict:fetch_keys(Dict),
    Facts = prove(Querys2, Trees),
    Dict,
    
    ETxs = "g2wAAAAEaARkAAZzaWduZWRoBmQAAmNhbQAAAEEEhVmGzXqC2hD+5Qy6OXlpK62kiYLi9rwx7CAK96HowS4OOgO+1CphnkV5hxSFj9AuOkIGteOq9O0WI3iWLQ2GOmEBYRRtAAAAQQRHXAXlfMl3JIv7Ni5NmiaAhuff/NsmnCCnWElvuaemWoQ2aCFJzogO/dHY9yrDUsIHaqtS+iD1OW3KuPrpBgoCYjuaygBtAAAAYE1FVUNJUUR5Q0p1Y2h6TlEzUXBkbTk4VjFkWGNxQklEUjVlNDFoRWtlMGRvUkVNd2hBSWdKbjcza3hISzhNUXZDVUttcGEzbzRSWkJYR3FoMXNWV2NZZXNyQ3NRVlo4PWpoBGQABnNpZ25lZGgGZAACY2FtAAAAQQSFWYbNeoLaEP7lDLo5eWkrraSJguL2vDHsIAr3oejBLg46A77UKmGeRXmHFIWP0C46Qga146r07RYjeJYtDYY6YQJhFG0AAABBBFRjuCgudSTRU79SVoCBvWi55+N1QethvQI6LKUCoEPHvIfedkQLxnuD2VJHqoLrULmXyexRWs2sOTwyLsdyL+FiO5rKAG0AAABgTUVVQ0lRRG1naWwvSkxGRVJaN05LUEpZMHZFQ21nZUlsNFdkdU5SbmlzWkw2R25ZVFFJZ1dBOExUazNENEVva3EvWUY4U3d4SnljR1Ixd2RLejlRMWpJUmpyeEFzSDQ9amgEZAAGc2lnbmVkaApkAAJuY20AAABBBIVZhs16gtoQ/uUMujl5aSutpImC4va8MewgCveh6MEuDjoDvtQqYZ5FeYcUhY/QLjpCBrXjqvTtFiN4li0NhjptAAAAQQRUY7goLnUk0VO/UlaAgb1ouefjdUHrYb0COiylAqBDx7yH3nZEC8Z7g9lSR6qC61C5l8nsUVrNrDk8Mi7Hci/hYTJhA2IAACcQYgAAJxFhAmEEYQFtAAAAYE1FWUNJUUQ4U1hNeUYxQmRnbWRaRVdHbWFFR3JncXRxTXUvRGZJYmZVMnE1eE94ZUdnSWhBTTU3L21wcmFucDdiVTBSK2RoMS9wZjBOeHViVWJIU256UEFrcFY5b1gwNW0AAABgTUVVQ0lIeTdhenJyYmxIdzdSdEVmRVRMcU5ERTdCUUhmb1Rnd29CVHlZV0JKcHd0QWlFQWxPcnRhY1k1NVFSNUZUVUpoVFltbW5TWldtSGZ4cFUvbmExbjJsSVhJdm89aARkAAZzaWduZWRoCmQAAm5jbQAAAEEER1wF5XzJdySL+zYuTZomgIbn3/zbJpwgp1hJb7mnplqENmghSc6IDv3R2Pcqw1LCB2qrUvog9Tltyrj66QYKAm0AAABBBFRjuCgudSTRU79SVoCBvWi55+N1QethvQI6LKUCoEPHvIfedkQLxnuD2VJHqoLrULmXyexRWs2sOTwyLsdyL+FhMmEBYgAAJxBiAAAnEWECYQRhAm0AAABgTUVRQ0lCZHlWUUhxRlZyQWFGMTVsN0NmajlyckU5THI3RFFUWVJrc3c5d3dMek1nQWlBOGZrMXpIVVgwdlN6b0dVQ05JTGRmRER5Y2lNMnlWVldLb0pnTGNUbUZhdz09bQAAAGBNRVFDSUJvV3pJQU9oUExqTXJjN0tnV3ZFOUxhWmdXdllqYTY0Mk10YzE0S3RFdXNBaUFhRktDTmNhQUFSck9NUVNCUmZMKzdPV054aHduaWdwRUZBc1JaL0c3MmVBPT1q",
    %Txs = binary_to_term(base64:decode(ETxs)),
    {Pub30, Priv30} = sign2:new_key(),
    {Pub4, _} = sign2:new_key(),
    NewTx = create_account_tx:make_dict(Pub30, 10, 10, keys:pubkey()),
    NewTx2 = create_account_tx:make_dict(Pub4, 10, 10, keys:pubkey()),
    CID = <<7:256>>,
    NewTx3 = new_channel_tx:make_dict(CID, keys:pubkey(), Pub3, 1, 1, 1, 1),
    Txs = [keys:sign(NewTx),
           keys:sign(NewTx2)],
    Q2 = txs_to_querys2(Txs, Trees, 1),
    prove(Q2, Trees),
    success.
    
    

