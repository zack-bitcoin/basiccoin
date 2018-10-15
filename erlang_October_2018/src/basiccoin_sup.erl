-module(basiccoin_sup).
-behaviour(supervisor).
-export([start_link/0, init/1, stop/0]).

-define(CHILD(I, Type), {I, {I, start_link, []}, permanent, 5000, Type, [I]}).
-define(keys, [sync_kill, sync_mode, keys, recent_blocks, block_hashes, headers, block_absorber, block_organizer, tx_pool, tx_pool_feeder, mine, sync, tree_data, potential_block, push_block, found_block_timer]).
start_link() -> 
    supervisor:start_link({local, ?MODULE}, ?MODULE, []).
child_killer([]) -> [];
child_killer([H|T]) -> 
    supervisor:terminate_child(?MODULE, H),
    child_killer(T).
stop() -> 
    child_killer(lists:reverse(?keys)).

child_maker([]) -> [];
child_maker([H|T]) -> [?CHILD(H, worker)|child_maker(T)].
tree_child(Id, KeySize, Size) ->
    tree_child(Id, KeySize, Size, 0).
tree_child(Id, KeySize, Size, Meta) ->
    Amount = 2000000,
    Sup = list_to_atom(atom_to_list(Id) ++ "_sup"),
    {Sup, {trie_sup, start_link, [KeySize, Size, Id, Amount, Meta, constants:hash_size(), hd]}, permanent, 5000, supervisor, [trie_sup]}.

init([]) ->
    HS = constants:hash_size(),
    Trees = [tree_child(accounts, HS, constants:account_size())],
    Children = child_maker(?keys),
    io:fwrite("basiccoin sup"),
    {ok, { {one_for_one, 50000, 1}, Trees ++ Children} }.
