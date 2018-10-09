-module(constants).
-compile(export_all).

hash_size() -> 32.
balance_bits() -> 48.
account_nonce_bits() -> 24.
pubkey_size() -> 65.%bytes
account_size() -> ((balance_bits() + account_nonce_bits()) div 8) + pubkey_size().
root0() -> 1.
    
