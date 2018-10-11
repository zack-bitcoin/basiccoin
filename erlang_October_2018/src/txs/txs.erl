-module(txs).
-export([digest_from_dict/3, developer_lock/3, key2module/1]).
digest_from_dict([C|T], Dict, H) ->
    case element(1, C) of
        coinbase ->
            NewDict = coinbase_tx:go(C, Dict, H),
            digest_from_dict3(T, NewDict, H);
        signed -> digest_from_dict3([C|T], Dict, H)
    end.
digest_from_dict3([], Dict, _) -> Dict;
digest_from_dict3([STx|T], Dict, Height) ->
    true = testnet_sign:verify(STx),
    Tx = testnet_sign:data(STx),
    NewDict = digest_from_dict2(Tx, Dict, Height),
    digest_from_dict3(T, NewDict, Height).
key2module(multi_tx) -> multi_tx;
key2module(create_acc_tx) -> create_account_tx;
key2module(spend) -> spend_tx;
key2module(delete_acc_tx) -> delete_account_tx;
key2module(nc) -> new_channel_tx;
key2module(ctc) -> channel_team_close_tx;
key2module(csc) -> channel_solo_close;
key2module(timeout) -> channel_timeout_tx;
key2module(cs) -> channel_slash_tx;
key2module(ex) -> existence_tx;
key2module(oracle_new) -> oracle_new_tx;
key2module(oracle_bet) -> oracle_bet_tx;
key2module(oracle_close) -> oracle_close_tx;
key2module(unmatched) -> oracle_unmatched_tx;
key2module(oracle_winnings) -> oracle_winnings_tx;
key2module(coinbase_old) -> coinbase_tx.
digest_from_dict2(Tx, Dict, H) ->
    Fee = element(4, Tx),
    true = Fee > 0,
    Key = element(1, Tx),
    M = key2module(Key),
    M:go(Tx, Dict, H, true).
developer_lock(From, NewHeight, Dict) ->
    case application:get_env(amoveo_core, kind) of
	{ok, "production"} ->
	    MP = constants:master_pub(),
	    if
		From == MP ->
		    BP = governance:dict_get_value(block_period, Dict),
		    HeightSwitch = (10 * constants:developer_lock_period()) div BP,
		    true = NewHeight > HeightSwitch;
		true -> ok
	    end;
	_ -> ok
    end.
    
