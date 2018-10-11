-module(constants).
-compile(export_all).

hash_size() -> 32.
balance_bits() -> 48.
account_nonce_bits() -> 24.
pubkey_size() -> 65.%bytes
account_size() -> ((balance_bits() + account_nonce_bits()) div 8) + pubkey_size().
height_bits() -> 32.
time_bits() -> 40.
version_bits() -> 16.

root0() -> 1.
initial_difficulty() -> 1.
external_port() -> 8060.
internal_port() -> 8061.
headers_file() -> "data/headers.db".
block_hashes() -> "data/block_hashes.db".
recent_blocks() -> "data/recent_blocks.db".
    
