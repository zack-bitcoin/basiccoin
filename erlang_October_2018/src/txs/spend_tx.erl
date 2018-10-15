-module(spend_tx).
-export([go/4, make/5, make_dict/4, from/1, to/1]).
-include("../records.hrl").
from(X) -> X#spend.from.
to(X) -> X#spend.to. 
make_dict(To, Amount, Fee, From) ->
    Acc = trees:dict_tree_get(accounts, From),
    #spend{from = From, nonce = Acc#account.nonce + 1, to = To, amount = Amount, fee = Fee}.
	    
make(To, Amount, Fee, From, Trees) ->
    Accounts = trees:accounts(Trees),
    {_, Acc, Proof} = accounts:get(From, Accounts),
    {_, _Acc2, Proof2} = accounts:get(To, Accounts),
    Tx = #spend{from = From, nonce = Acc#account.nonce + 1, to = To, amount = Amount, fee = Fee},
    {Tx, [Proof, Proof2]}.
go(Tx, Dict, NewHeight, NonceCheck) ->
    case Tx#spend.version of
        0 -> ok;
        N -> N = version:doit(NewHeight)
    end,
    From = Tx#spend.from,
    To = Tx#spend.to,
    false = From == To,
    A = Tx#spend.amount,
    true = (A > 0),
    Nonce = if
		NonceCheck -> Tx#spend.nonce;
		true -> none
	    end,
    Facc = accounts:dict_update(From, Dict, -A-Tx#spend.fee, Nonce),
    To0 = accounts:dict_get(To, Dict),
    Tacc = case To0 of
	       empty -> accounts:new(To, A);
	       _ -> accounts:dict_update(To, Dict, A, none)
	   end,
    Dict2 = accounts:dict_write(Facc, Dict),
    accounts:dict_write(Tacc, Dict2).
