-module(sync_mode).
-behaviour(gen_server).
-export([start_link/0,code_change/3,handle_call/3,handle_cast/2,handle_info/2,init/1,terminate/2,
	quick/0, normal/0, check/0, check_switch_to_normal/0]).
init(ok) -> 
    Kind = constants:mode(),
    X = case Kind of
	    "production" -> quick;
	    _ -> normal
	end,
    {ok, X}.
start_link() -> gen_server:start_link({local, ?MODULE}, ?MODULE, ok, []).
code_change(_OldVsn, State, _Extra) -> {ok, State}.
terminate(_, _) -> io:format("died!"), ok.
handle_info(_, X) -> {noreply, X}.
handle_cast(_, X) -> {noreply, X}.
handle_call(quick, _From, _) -> 
    {reply, quick, quick};
handle_call(normal, _From, _) -> 
    {reply, normal, normal};
handle_call(_, _From, X) -> {reply, X, X}.

quick() ->
    gen_server:call(?MODULE, quick).
normal() ->
    gen_server:call(?MODULE, normal).
check() ->
    gen_server:call(?MODULE, check).

check_switch_to_normal() ->
    check_switch_to_normal(0, now(), 0).
check_switch_to_normal(N, BlockTime, Counter) ->
    go = sync_kill:status(),
    T1 = found_block_timer:get(),
    T3 = timer:now_diff(now(), BlockTime),
    S2 = T3 / 1000,
    Portion = 0.9,
    IPortion = 0.1,
    %1 = Portion + IPortion,
    N3 = (N * Portion) + (S2 * IPortion),
    %io:fwrite("check switch to normal "),
    
%%io:fwrite(integer_to_list(round(N3))),
    io:fwrite("\n"),
    if
	N3 > 6000 ->
	    sync:stop(),
	    sync_mode:normal();
	not(T1 == BlockTime) ->
	    T = timer:now_diff(T1, BlockTime),
	    S = T / 1000, %miliseconds
	    N2 = (N * Portion) + (S * IPortion),
	    check_switch_to_normal(N2, T1, Counter + 1);
	true ->
	    io:fwrite("syncing...\n"),
	    if
		S2 > 5000 ->
		%((Counter rem 15) == 0) ->
		    sync:start(),
		    timer:sleep(3000);
		true -> ok
	    end,
	    timer:sleep(1000),
	    check_switch_to_normal(N, T1, Counter + 1)
    end.

   % T1 = block_absorber:check(),%This is really bad. the timer restarts every time someone even attempts to give us a block. even if it is not a new block.
%T = timer:now_diff(now(), T1),
%    S = T / 1000000,%seconds
%    if
%	S > 180 -> 
%	    sync:stop(),
%	    sync_mode:normal();
%	true -> 
%	    sync:start(),
%	    timer:sleep(15000),
%	    check_switch_to_normal()
%    end.
	    
