-module(ext_handler).

-export([init/3, handle/2, terminate/3, doit/1]).
%example of talking to this handler:
%httpc:request(post, {"http://127.0.0.1:3010/", [], "application/octet-stream", "echo"}, [], []).
%curl -i -d '["test"]' http://localhost:3011
%curl -i -d echotxt http://localhost:3010

init(_Type, Req, _Opts) -> {ok, Req, no_state}.
terminate(_Reason, _Req, _State) -> ok.
handle(Req, State) ->
    {ok, Data, Req2} = cowboy_req:body(Req),
    {{IP, _}, Req3} = cowboy_req:peer(Req2),
    D = case request_frequency:doit(IP) of
	    ok ->
		true = is_binary(Data),
		A = packer:unpack(Data),
		B = doit(A),
		packer:pack(B);
	    _ -> 
		packer:pack({ok, <<"stop spamming the server">>})
	end,	    

    Headers = [{<<"content-type">>, <<"application/octet-stream">>},
	       {<<"Access-Control-Allow-Origin">>, <<"*">>}],
    {ok, Req4} = cowboy_req:reply(200, Headers, D, Req3),
    {ok, Req4, State}.
doit({test}) -> {ok, 0};
doit(_) ->
    1=2,
    {ok, error}.
