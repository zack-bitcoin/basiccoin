-module(basiccoin_app).

-behaviour(application).

%% Application callbacks
-export([start/2, stop/1]).

start(_StartType, _StartArgs) ->
    application:start(inets),
    inets:start(),
    servers:start(),
    utils:make_block_folders(),
    io:fwrite("starting node\n"),
    basiccoin_sup:start_link().

%%--------------------------------------------------------------------
stop(_State) ->
    ok.

%%====================================================================
%% Internal functions
%%====================================================================
