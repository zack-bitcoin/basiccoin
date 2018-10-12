-module(tree_data).
-behaviour(gen_server).
-export([start_link/0,code_change/3,handle_call/3,handle_cast/2,handle_info/2,init/1,terminate/2,
	dict_update_trie/2, garbage/2, remove_before/2]).
-include("../records.hrl").
init(ok) -> {ok, []}.
start_link() -> gen_server:start_link({local, ?MODULE}, ?MODULE, ok, []).
code_change(_OldVsn, State, _Extra) -> {ok, State}.
terminate(_, _) -> io:format("died!"), ok.
handle_info(_, X) -> {noreply, X}.
handle_cast(_, X) -> {noreply, X}.
handle_call({remove_before, Blocks, Work}, _, _) -> 
    B2 = remove_before_internal(Blocks, Work),
    {reply, B2, []};
handle_call({garbage, Trash, Keep}, _, _) -> 
    internal(Trash, Keep, fun(A, B, C) -> trie:garbage(A, B, C) end),
    {reply, ok, []};
%handle_call({prune, Trash, Keep}, _, _) -> 
%    internal(Trash, Keep, fun(A, B, C) -> trie:prune(A, B, C) end),
%    {reply, ok, []};
handle_call({update, Trees, Dict}, _From, _) -> 
    Y = internal_dict_update_trie(Trees, Dict),
    {reply, Y, []};
handle_call(_, _From, X) -> {reply, X, X}.

remove_before(Blocks, Work) ->
    gen_server:call(?MODULE, {remove_before, Blocks, Work}).
dict_update_trie(Trees, Dict) ->
    gen_server:call(?MODULE, {update, Trees, Dict}).
garbage(Trash, Keep) ->
    gen_server:call(?MODULE, {garbage, Trash, Keep}).
internal(PruneBlock, KeepBlock, F) ->
    Trees = [accounts],
    [A] = 
	lists:map(fun(T) ->
			  T1 = PruneBlock#block.trees,
			  T2 = KeepBlock#block.trees,
			  A1 = trees:T(T1),
			  A2 = trees:T(T2),
			  F(A1, A2, T)
		  end, Trees),
    ok.

internal_dict_update_trie(Trees, Dict) ->
    %do the orders and oracle_bets last, then insert their state roots into the accounts and oracles.
    %pointers are integers, root hashes are binary.
    Keys = dict:fetch_keys(Dict),
    {Accounts, Keys1} = get_things(accounts, Keys),
    %{leaf, key, val, meta}
    AccountLeaves = dict_update_trie_account(Trees, Accounts, Dict, []),
    AT = trees:accounts(Trees),
    trie:put_batch(AccountLeaves, AT, accounts).


keys2leaves([], _, _) -> [];
keys2leaves([H|T], Type, Dict) ->
    {Type, Key} = H,
    New = Type:dict_get(Key, Dict),
    I = Type:key_to_int(Key),
    L = case New of
	    empty -> leaf:new(I, empty, 0, trie:cfg(Type));
	    _ ->
		Value = Type:serialize(New),
		leaf:new(I, Value, 0, trie:cfg(Type))
	end,
    [L|keys2leaves(T, Type, Dict)].
dict_update_trie_account(_, [], _, X) -> X;
dict_update_trie_account(Trees, [H|T], Dict, X) ->
    X2 = dict_update_account_oracle_helper(accounts, H, bets, Trees, constants:root0(), update_bets, Dict, X),
    dict_update_trie_account(Trees, T, Dict, X2).
dict_update_account_oracle_helper(Type, H, Type2, Trees, EmptyType2, UpdateType2, Dict, Leaves) ->
    Type = accounts,
    {_, Key} = H,%key is your pubkey
    New0 = Type:dict_get(Key, Dict),
    Tree = trees:Type(Trees),
    Leaves2 = 
        case New0 of
            empty -> 
		L = leaf:new(Type:key_to_int(Key), empty, 0, trie:cfg(Type)),
                [L|Leaves];
            _ -> 
		New = New0,
		L = leaf:new(Type:key_to_int(Key), Type:serialize(New), 0, trie:cfg(Type)),
                [L|Leaves]
    end,
    Leaves2.
get_things(Key, L) ->
    get_things(Key, L, [], []).
get_things(Key, [], A, B) -> {A, B};
get_things(Key, [{Key, X}|L], A, B) ->
    get_things(Key, L, [{Key, X}|A], B);
get_things(Key, [{Key2, X}|L], A, B) ->
    get_things(Key, L, A, [{Key2, X}|B]).
remove_before_internal([], _) -> [];
remove_before_internal([{Hash, TotalWork}|T], X) when TotalWork < X ->
    KeepBlock = block:get_by_hash(Hash),
    Height = KeepBlock#block.height,
    if
	Height < 2 -> ok;
	true ->
	    H = KeepBlock#block.prev_hash,
	    OldBlock = block:get_by_hash(H),
	    internal(OldBlock, KeepBlock, fun(A, B, C) -> trie:garbage(A, B, C) end)
	    %tree_data:garbage(OldBlock, KeepBlock)
    end,
    remove_before_internal(T, X);
remove_before_internal([H|T], X) -> [H|remove_before_internal(T, X)].



    
