-module(utils).
-compile(export_all).

start() -> application:ensure_all_started(basiccoin).
binary_to_file_path(Code, Binary) ->
    Code = blocks,
    <<Byte, _/binary>> = Binary,
    H = to_hex(<<Byte>>),
    %Encoded = base58:binary_to_base58(Binary),
    Encoded = to_hex(Binary),
    "data/blocks/" ++ H ++ "/" ++ Encoded ++ ".db".
to_hex(<<>>) -> 
      [];
to_hex(<<A:4, B/bitstring>>) ->
    if
        A < 10 -> [(A+48)|to_hex(B)];
        true -> [(A+87)|to_hex(B)]
    end.
make_block_folders() ->
    mbf(0).
mbf(256) -> ok;
mbf(N) ->    
    Code = blocks,
    H = to_hex(<<N>>),
    os:cmd("mkdir data/blocks/"++H),
    mbf(N+1).
