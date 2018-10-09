-module(sign2).
-export([new_key/0]).
params() -> crypto:ec_curve(secp256k1).
new_key() -> crypto:generate_key(ecdh, params()).
