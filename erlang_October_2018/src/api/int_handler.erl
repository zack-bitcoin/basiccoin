-module(int_handler).
-export([init/3, handle/2, terminate/3, doit/1]).
%example of talking to this handler:
%httpc:request(post, {"http://127.0.0.1:3011/", [], "application/octet-stream", packer:pack({pubkey})}, [], []).
%curl -i -d '[-6,"test"]' http://localhost:3011
handle(Req, State) ->
    {ok, Data, _} = cowboy_req:body(Req),
    true = is_binary(Data),
    %io:fwrite("\ngot this data \n"),
    %io:fwrite(Data),
    %io:fwrite("\n"),
    A = packer:unpack(Data),
    B = doit(A),
    D = packer:pack(B),
    Headers = [{<<"content-type">>, <<"application/octet-stream">>},
    {<<"Access-Control-Allow-Origin">>, <<"*">>}],
    {ok, Req2} = cowboy_req:reply(200, Headers, D, Req),
    {ok, Req2, State}.
init(_Type, Req, _Opts) -> {ok, Req, no_state}.
terminate(_Reason, _Req, _State) -> ok.
doit({Key}) ->
    {ok, api:Key()};
doit({Key, Arg1}) ->
    {ok, api:Key(Arg1)};
doit({Key, Arg1, Arg2}) ->
    {ok, api:Key(Arg1, Arg2)};
doit({Key, A, B, C}) ->
    {ok, api:Key(A, B, C)};
doit({Key, A, B, C, D}) ->
    {ok, api:Key(A, B, C, D)};
doit({Key, A, B, C, D, E}) ->
    {ok, api:Key(A, B, C, D, E)};
doit({Key, A, B, C, D, E, F}) ->
    {ok, api:Key(A, B, C, D, E, F)};
doit({Key, A, B, C, D, E, F, G}) ->
    {ok, api:Key(A, B, C, D, E, F, G)};
doit({Key, A, B, C, D, E, F, G, H}) ->
    {ok, api:Key(A, B, C, D, E, F, G, H)};
doit({Key, A, B, C, D, E, F, G, H, I}) ->
    {ok, api:Key(A, B, C, D, E, F, G, H, I)};
doit({Key, A, B, C, D, E, F, G, H, I, J}) ->
    {ok, api:Key(A, B, C, D, E, F, G, H, I, J)};

doit(X) ->
    io:fwrite("don't know how to handle it \n"),
    io:fwrite(packer:pack(X)),
    io:fwrite("\n"),
    {error}.
    
