
-record(key, {pub, id}). %used for shared, oracle_bets, and orders
-record(header, {height,
                 prev_hash,
                 trees_hash,
                 txs_proof_hash,
                 time,
                 difficulty,
                 version,
                 nonce,
                 accumulative_difficulty = 0,
                 period}).
-record(block, {height,
                prev_hash,
                trees_hash,
                time,
                difficulty,
                period,
                version,
                nonce = 0,
                trees,
                txs,
                prev_hashes = {prev_hashes},
                proofs = [],
                roots,
                hash = <<>>,
		market_cap = 0}).
-record(acc, {balance = 0, %amount of money you have
	      nonce = 0, %increments with every tx you put on the chain. 
	      pubkey = <<>>,
	      bets = 1,%This is a pointer to the merkel tree that stores how many bets you have made in each oracle.
              bets_hash = <<>>}).
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