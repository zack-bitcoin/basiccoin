-module(constants).
-compile(export_all).

mode() -> "production".

%sizes for serialized objects.
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
block_reward() -> 100000000.
burn_fee() -> 100000.%so 1 block reward pays for 100 txs
    
block_period() -> 100.
time_units() -> 100.%0.1 seconds
start_time() -> 15192951759.
max_block_size() -> 1000000.
    
    

%Below this line can be customized on each node. Above this line needs to be the same for all the nodes on the same blockchain.

external_port() -> 8060.
internal_port() -> 8061.

headers_file() -> "data/headers.db".
block_hashes() -> "data/block_hashes.db".
recent_blocks() -> "data/recent_blocks.db".
keys() -> "keys.db".
recent_blocks_period() -> 3. %this is how frequently we calculate which blocks should no longer be tracked for pruning.
    
    
