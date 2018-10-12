-module(tester).
-export([test/0]).
test() ->
    unlocked = keys:status(),
    success = accounts:test(),
    success = block:test(),
    success = test_txs:test(),
    success.
