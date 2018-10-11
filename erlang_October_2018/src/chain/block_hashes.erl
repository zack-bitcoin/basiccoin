-module(block_hashes).
% keep the hash of every block we attempt to verify, that way we don't waste time trying to verify the same block twice.
%each blockhash is about 32 bytes. We need to prepare for about 10000000 blocks. So that would be 32 megabytes of data. We can keep this all in ram.
-behaviour(gen_server).
-export([start_link/0,code_change/3,handle_call/3,handle_cast/2,handle_info/2,init/1,terminate/2, 
	 add/1,check/1,test/0]).
-record(d, {set, list = []}).
-define(LOC, constants:block_hashes()).
init(ok) -> 
    process_flag(trap_exit, true),
    X = db:read(?LOC),
    K = if
	    X == "" -> #d{set = i_new()};
	    %i_new();
	    true -> X
	end,
    {ok, K}.
start_link() -> gen_server:start_link({local, ?MODULE}, ?MODULE, ok, []).
code_change(_OldVsn, State, _Extra) -> {ok, State}.
terminate(_, X) -> 
    db:save(?LOC, X),
    io:format("block_hashes died!"), ok.
handle_info(_, X) -> {noreply, X}.
handle_cast(_, X) -> {noreply, X}.
handle_call({add, H}, _From, X) ->
    N = i_insert(H, X#d.set),
    L2 = [H|X#d.list],
    Len = length(L2),
    X2 = if
	     Len > 500 ->
		 {NL, T} = lists:split(400, L2),
		 NS = remove_many(T, N),
		 X#d{list = NL, set = NS};
	     true ->
		 X#d{list = L2, set = N}
	 end,
    db:save(?LOC, X2),%This line is only necessary for power failures
    {reply, ok, X2};
handle_call({check, H}, _From, X) ->
    B = i_check(H, X#d.set), 
    {reply, B, X} ;
handle_call(_, _From, X) -> {reply, X, X}.

remove_many([], N) -> N;
remove_many([H|T], N) ->
    N2 = i_remove(H, N),
    remove_many(T, N2).

add(X) -> 
    true = is_binary(X),
    true = size(X) == constants:hash_size(),
    gen_server:call(?MODULE, {add, X}).

check(X) ->
    true = size(X) == constants:hash_size(),
    gen_server:call(?MODULE, {check, X}).

i_new() ->
    %gb_sets:new().
    sets:new().
i_insert(H, X) ->
    %gb_sets:add(H, X).
    sets:add_element(H, X).
i_check(H, X) ->
    %gb_sets:is_member(H, X).
    sets:is_element(H, X).
i_remove(H, X) ->
    sets:del_element(H, X).

test() ->
    V1 = <<1:92>>,
    V2 = <<2:92>>,
    D = i_new(),
    D2 = i_insert(V1, D),
    false = i_check(V2, D2),
    true = i_check(V1, D2),
    success.
