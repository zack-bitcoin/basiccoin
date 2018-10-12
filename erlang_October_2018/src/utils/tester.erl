-module(tester).
-export([test/0]).
test() ->
    success = accounts:test(),
    success = block:test(),
    success.
