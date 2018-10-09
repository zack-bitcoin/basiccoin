-module(accounts).
-export([new/2, write/2, get/2, delete/2,
         dict_update/4, dict_get/2, dict_write/2, dict_delete/2,%update dict stuff
	 verify_proof/4,make_leaf/3,key_to_int/1,serialize/1,test/0, deserialize/1]).%common tree stuff
-record(account, {balance = 0, nonce = 0, pubkey = <<>>}).
-define(id, accounts).
new(Pub, Balance) ->
    %Root0 = constants:root0(),
    #account{pubkey = Pub, balance = Balance, nonce = 0}.
dict_update(Pub, Dict, Amount, NewNonce) ->
    Account = dict_get(Pub, Dict),
    OldNonce = Account#account.nonce,
    FinalNonce = case NewNonce of
                     none ->
                         Account#account.nonce;
                     NewNonce ->
                         true = ((NewNonce - 1) == OldNonce),
                         NewNonce
                 end,
    NewBalance = Amount + Account#account.balance,
    true = NewBalance > 0,
    Account#account{balance = NewBalance,
		    nonce = FinalNonce}.
key_to_int(X) ->
    trees:hash2int(ensure_decoded_hashed(X)).
dict_get(Key, Dict) ->
    %X = dict:fetch({accounts, Key}, Dict),
    X = dict:find({accounts, Key}, Dict),
    case X of
        error -> empty;
        {ok, 0} -> empty;
        {ok, Y} -> Y
    end.
get(Pub, Accounts) ->
    PubId = key_to_int(Pub),
    {RH, Leaf, Proof} = trie:get(PubId, Accounts, ?id),
    Account = case Leaf of
                  empty -> empty;
                  Leaf -> deserialize(leaf:value(Leaf))
              end,
    {RH, Account, Proof}.
dict_write(Account, Dict) ->
    Pub = Account#account.pubkey,
    Out = dict:store({accounts, Pub}, 
                     serialize(Account),
                     Dict),
    Out.
write(Account, Root) ->
    Pub = Account#account.pubkey,
    SizePubkey = constants:pubkey_size(),
    SizePubkey = size(Pub),
    SerializedAccount = serialize(Account),
    true = size(SerializedAccount) == constants:account_size(),
    PubId = key_to_int(Pub),
    trie:put(PubId, SerializedAccount, 0, Root, ?id). % returns a pointer to the new root
dict_delete(Pub, Dict) ->
    dict:store({accounts, Pub}, 0, Dict).
delete(Pub0, Accounts) ->
    PubId = key_to_int(Pub0),
    trie:delete(PubId, Accounts, ?id).
serialize(Account) ->
    true = size(Account#account.pubkey) == constants:pubkey_size(),
    BalanceSize = constants:balance_bits(),
    NonceSize = constants:account_nonce_bits(),
    SerializedAccount =
        <<(Account#account.balance):BalanceSize,
          (Account#account.nonce):NonceSize,
          (Account#account.pubkey)/binary>>,
    true = size(SerializedAccount) == constants:account_size(),
    SerializedAccount.
deserialize(SerializedAccount) ->
    BalanceSize = constants:balance_bits(),
    NonceSize = constants:account_nonce_bits(),
    SizePubkey = constants:pubkey_size(),
    PubkeyBits = SizePubkey * 8,
    <<Balance:BalanceSize,
      Nonce:NonceSize,
      Pubkey:PubkeyBits>> = SerializedAccount,
    #account{balance = Balance,
         nonce = Nonce,
         pubkey = <<Pubkey:PubkeyBits>>}.
ensure_decoded_hashed(Pub) ->
    HashSize = constants:hash_size(),
    PubkeySize = constants:pubkey_size(),
    case size(Pub) of
        HashSize -> Pub;
        PubkeySize ->
            hash:doit(Pub);
        _ ->
            hash:doit(base64:decode(Pub))
    end.
make_leaf(Key, V, CFG)  ->
    leaf:new(key_to_int(Key),
             V, 0, CFG).
verify_proof(RootHash, Key, Value, Proof) ->
    trees:verify_proof(?MODULE, RootHash, Key, Value, Proof).
test() ->
    {Pub, _Priv} = sign2:new_key(),
    Acc = new(Pub, 0),
    S = serialize(Acc),
    Acc = deserialize(S),
    Root0 = constants:root0(),
    NewLoc = write(Acc, Root0),
    {Root, Acc, Proof} = get(Pub, NewLoc),
    true = verify_proof(Root, Pub, serialize(Acc), Proof),
    {Root2, empty, Proof2} = get(Pub, Root0),
    true = verify_proof(Root2, Pub, 0, Proof2),
    success.
    

    
