-module(push_block).
-behaviour(gen_server).
-export([start_link/0,code_change/3,handle_call/3,handle_cast/2,handle_info/2,init/1,terminate/2,
	cron/0, add/1]).
init(ok) -> 
    {ok, []}.
start_link() -> gen_server:start_link({local, ?MODULE}, ?MODULE, ok, []).
code_change(_OldVsn, State, _Extra) -> {ok, State}.
terminate(_, _) -> io:format("died!"), ok.
handle_info(_, X) -> {noreply, X}.
handle_cast({add, Block}, X) -> 
    {noreply, {now(), Block}};
handle_cast(cron, X) -> 
    {ok, Kind} = application:get_env(amoveo_core, kind),
    SLimit = case Kind of
		 "production" -> 10;
		 _ -> 1
	     end,
    X2 = case X of
	     [] -> [];
	     {N, B} -> 
		 T = timer:now_diff(now(), N),
		 S = T / 1000000,%to seconds
		 if
		     S < SLimit -> X;
		     true ->
			 sync:push_new_block(B),%only do this once every 3 seconds at most.
			 []
		 end
	 end,
    {noreply, X2};
handle_cast(_, X) -> {noreply, X}.
handle_call(_, _From, X) -> {reply, X, X}.

add(Block) ->
    gen_server:cast(?MODULE, {add, Block}).
cron() ->
    spawn(fun() ->
		  timer:sleep(1000),
		  cron2()
	  end).
cron2() ->
    gen_server:cast(?MODULE, cron),
    timer:sleep(200),
    cron2().
