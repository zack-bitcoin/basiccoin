-module(sign2).
-export([new_key/0, verify_tx/1]).
-include("../records.hrl").
params() -> crypto:ec_curve(secp256k1).
new_key() -> crypto:generate_key(ecdh, params()).
verify_tx(ST) ->
    Tx = ST#signed.data,
    Pub = element(2, Tx),
    Type = element(1, Tx),
    sign:verify_sig(Tx, ST#signed.sig, Pub).
    
