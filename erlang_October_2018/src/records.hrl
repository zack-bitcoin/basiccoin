
-record(key, {pub, id}). %used for shared, oracle_bets, and orders
-record(header, {height,
                 prev_hash,
                 trees_hash,
                 txs_proof_hash,
                 time,
                 difficulty,
                 version,
                 nonce,
                 accumulative_difficulty = 0}).
-record(block, {height,
                prev_hash,
                trees_hash,
                time,
                difficulty,
                version,
                nonce = 0,
                trees,
                txs,
                prev_hashes = {prev_hashes},
                proofs = [],
                roots,
                hash = <<>>,
		market_cap = 0}).
-record(account, {balance = 0, nonce = 0, pubkey = <<>>}).
-record(tx_pool, {txs = [],
                  %trees,%this changes once per tx
                  block_trees,%this changes once per block
                  dict = dict:new(), %mirrors trees.
                  facts = [], 
                  height = 0,
		  bytes = 2,
		  checksums = []}).
-record(spend, {from = 0,
	       nonce = 0,
	       fee = 0,
	       to = 0,
	       amount = 0,
	       version = 0}).
-record(signed, {data, sig}).	  