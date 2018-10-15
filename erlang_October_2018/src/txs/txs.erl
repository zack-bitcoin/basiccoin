-module(txs).
-export([digest_from_dict/3, key2module/1]).
-include("../records.hrl").
digest_from_dict([C|T], Dict, H) ->
    case element(1, C) of
        coinbase ->
            NewDict = coinbase_tx:go(C, Dict, H),
            digest_from_dict3(T, NewDict, H);
        signed -> digest_from_dict3([C|T], Dict, H)
    end.
digest_from_dict3([], Dict, _) -> Dict;
digest_from_dict3([STx|T], Dict, Height) ->
    true = sign2:verify_tx(STx),
    Tx = STx#signed.data,
    %Tx = testnet_sign:data(STx),
    NewDict = digest_from_dict2(Tx, Dict, Height),
    digest_from_dict3(T, NewDict, Height).
key2module(spend) -> spend_tx;
key2module(coinbase_old) -> coinbase_tx.
digest_from_dict2(Tx, Dict, H) ->
    Fee = element(4, Tx),
    true = Fee > 0,
    Key = element(1, Tx),
    M = key2module(Key),
    M:go(Tx, Dict, H, true).
    
