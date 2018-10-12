-module(sync_kill).
-behaviour(gen_server).
-export([start_link/0,code_change/3,handle_call/3,handle_cast/2,handle_info/2,init/1,terminate/2,
	status/0, stop/0, start/0]).
init(ok) -> {ok, go}.
start_link() -> gen_server:start_link({local, ?MODULE}, ?MODULE, ok, []).
code_change(_OldVsn, State, _Extra) -> {ok, State}.
terminate(_, _) -> io:format("died!"), ok.
handle_info(_, X) -> {noreply, X}.
handle_cast(start, _) -> {noreply, go};
handle_cast(stop, _) -> {noreply, stop};
handle_cast(_, X) -> {noreply, X}.
handle_call(status, _From, X) -> {reply, X, X};
handle_call(_, _From, X) -> {reply, X, X}.

status() -> gen_server:call(?MODULE, status).
stop() -> gen_server:cast(?MODULE, stop).
start() -> gen_server:cast(?MODULE, start).
