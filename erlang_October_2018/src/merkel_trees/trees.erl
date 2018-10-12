-module(trees).
-export([hash2int/1, verify_proof/5, new/1, root_hash/1,
	accounts/1, update_accounts/2]).

new(X) -> X.
root_hash(X) ->
    S = serialize_roots(X),
    hash:doit(S).
serialize_roots(X) ->
    trie:root_hash(accounts, X).

hash2int(X) ->
    U = size(X),
    U = constants:hash_size(),
    S = U*8,
    <<A:S>> = X,
    A.
verify_proof(TreeID, RootHash, Key, Value, Proof) ->
    CFG = trie:cfg(TreeID),
    V = case Value of
            0 -> empty;
            X -> X
        end,
    Leaf = TreeID:make_leaf(Key, V, CFG),
    verify:proof(RootHash, Leaf, Proof, CFG).
accounts(X) -> X.
update_accounts(_, X) -> X.
    
