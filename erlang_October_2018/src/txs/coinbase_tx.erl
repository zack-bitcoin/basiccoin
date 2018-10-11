-module(coinbase_tx).
-export([go/3, make/2, make_dict/1, from/1]).
-record(coinbase, {from = 0, nonce = 0, fee = 0}).
-include("../records.hrl").
from(X) -> X#coinbase.from.
make_dict(From) ->
    Acc = trees:dict_tree_get(accounts, From),
    #coinbase{from = From}.
make(From, Trees) ->
    Accounts = trees:accounts(Trees),
    {_, Acc, Proof} = accounts:get(From, Accounts),
    Tx = #coinbase{from = From},
    {Tx, [Proof]}.
go(Tx, Dict, NewHeight) ->
    From = Tx#coinbase.from,
    X = accounts:dict_get(From, Dict),
    %io:fwrite(Dict),%contains the key {governance, 1}, 
    BlockReward = governance:dict_get_value(block_reward, Dict),
    Nacc = case X of
               empty -> accounts:new(From, BlockReward);
               _ -> 
                   accounts:dict_update(From, Dict, BlockReward, none)
           end,
    Dict2 = accounts:dict_write(Nacc, Dict),
    DeveloperRewardVar = governance:dict_get_value(developer_reward, Dict),
    DeveloperReward = (BlockReward * DeveloperRewardVar) div 10000,
    M = accounts:dict_update(constants:master_pub(), Dict2, DeveloperReward, none),
    accounts:dict_write(M, Dict2).

