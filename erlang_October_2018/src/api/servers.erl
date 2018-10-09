-module(servers).
-export([start/0]).

start() ->
    ok = internal(),
    ok = external(),
    ok.

internal() ->
    Dispatch =
        cowboy_router:compile(
          [{'_', [{"/:file", int_file_handler, []},
                  {"/", int_handler, []}
                 ]}]),
    {ok, _} = cowboy:start_http(http_internal, 100,
                                [{ip, {127, 0, 0, 1}}, {port, constants:internal_port()}],
                                [{env, [{dispatch, Dispatch}]}]),
    ok.
external() ->
    Dispatch =
        cowboy_router:compile(
          [{'_', [{"/:file", ext_file_handler, []},
                  {"/", ext_handler, []}
                 ]}]),
    {ok, _} = cowboy:start_http(http, 100,
                                [{ip, {0, 0, 0, 0}}, {port, constants:external_port()}],
                                [{env, [{dispatch, Dispatch}]}]),
    ok.

    
