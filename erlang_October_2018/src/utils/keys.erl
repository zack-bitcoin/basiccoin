%the hard drive stores {f, pubkey, encrypted(privkey), encrypted("sanity")).
%the ram stores either {pubkey, privkey} or {pubkey, ""} depending on if this node is locked.
-module(keys).

-behaviour(gen_server).
-export([start_link/0,code_change/3,handle_call/3,handle_cast/2,handle_info/2,init/1,terminate/2, 
	 pubkey/0, sign/1, raw_sign/1, load/3, unlock/1,
	 lock/0, status/0, change_password/2, new/1,
	 shared_secret/1,
	 encrypt/2, decrypt/1, keypair/0,
	 test/0, format_status/2]).
%-define(LOC, "keys.db").
-define(LOC, constants:keys()).
-define(SANE(), <<"sanity">>).
start_link() -> gen_server:start_link({local, ?MODULE}, ?MODULE, ok, []).
code_change(_OldVsn, State, _Extra) -> {ok, State}.
terminate(_, _) -> io:fwrite("keys died. Possibly due to incorrect password.\n"), ok.
format_status(_,[_,_]) -> [{[], [{"State", []}]}].
-record(f, {pub = "", priv = "", sanity = ""}).
%sanity is only used on the hard drive, not in ram.
init(ok) -> 
    io:fwrite("start keys\n"),
    X = db:read(?LOC),
    Ka = if
	     X == "" -> 
		 {Pub1, Priv1} = 
		     sign:new_key(),
		 Pub = base64:decode(Pub1),
		 Priv = base64:decode(Priv1),
		 store(Pub, Priv, ""),
		 #f{pub = Pub, priv=Priv};
	     true -> #f{pub=X#f.pub}
	 end,
    erlang:send_after(1000, self(), set_initial_keys),
    {ok, Ka}.
store(Pub, Priv, Brainwallet) -> 
    true = size(Pub) == constants:pubkey_size(),
    X = #f{pub=Pub, priv=encryption:encrypt(Priv, Brainwallet), sanity=encryption:encrypt(?SANE(), Brainwallet)},
    db:save(?LOC, X),
    X.
handle_call({ss, Pub}, _From, R) ->
    {reply, utils:shared_secret(Pub, R#f.priv), R};
handle_call({raw_sign, _}, _From, R) when R#f.priv=="" ->
    {reply, "need to unlock passphrase", R};
handle_call({raw_sign, M}, _From, X) when not is_binary(M) ->
    {reply, "not binary", X};
handle_call({raw_sign, M}, _From, R) ->
    {reply, sign:sign(M, R#f.priv), R};
handle_call({sign, M}, _From, R) -> 
    {reply, utils:sign_tx(M, R#f.pub, R#f.priv), R};
handle_call(status, _From, R) ->
    Y = db:read(?LOC),
    Out = if
              Y#f.priv == "" -> empty;
              R#f.priv == "" -> locked;
              true -> unlocked
          end,
    {reply, Out, R};
handle_call(pubkey, _From, R) -> {reply, R#f.pub, R};
handle_call(keypair, _From, R) -> 
    Keys = case application:get_env(amoveo_core, test_mode, false) of
               true -> {R#f.pub, R#f.priv};
               _ -> none
           end,
    {reply, Keys, R};
handle_call({encrypt, Message, Pubkey}, _From, R) ->
    EM=encryption:send_msg(Message, base64:encode(Pubkey), base64:encode(R#f.pub), base64:encode(R#f.priv)),
    {reply, EM, R};
handle_call({decrypt, EMsg}, _From, R) ->
    io:fwrite("keys decrypt "),
    io:fwrite(packer:pack(EMsg)),
    io:fwrite("\n"),
    Message = encryption:get_msg(EMsg, base64:encode(R#f.priv)),
    %Message = encryption:get_msg(EMsg, R#f.priv),
    {reply, Message, R}.
handle_cast({load, Pub, Priv, Brainwallet}, _R) ->
    store(Pub, Priv, Brainwallet),
    {noreply, #f{pub=Pub, priv=Priv}};
handle_cast({new, Brainwallet}, _R) ->
    {Pub, Priv} = testnet_sign:new_key(),
    store(Pub, Priv, Brainwallet),
    {noreply, #f{pub=Pub, priv=Priv}};
handle_cast({unlock, Brainwallet}, _) ->
    X = db:read(?LOC),
    ?SANE() = encryption:decrypt(X#f.sanity, Brainwallet),
    Priv = encryption:decrypt(X#f.priv, Brainwallet),
    {noreply, #f{pub=X#f.pub, priv=Priv}};
handle_cast(lock, R) -> {noreply, #f{pub=R#f.pub}};
handle_cast({change_password, Current, New}, R) ->
    X = db:read(?LOC),
    ?SANE() = encryption:decrypt(X#f.sanity, Current),
    Priv = encryption:decrypt(X#f.priv, Current),
    store(R#f.pub, Priv, New),
    {noreply, R};
handle_cast(_, X) -> {noreply, X}.
handle_info(set_initial_keys, State) ->
    KeysEnvs = {application:get_env(amoveo_core, keys_pub),
                application:get_env(amoveo_core, keys_priv),
                application:get_env(amoveo_core, keys_pass)},
    case KeysEnvs of
        {{ok, Pub}, {ok, Priv}, {ok, Pass}} ->
	    Pub2 = base64:decode(Pub),
	    true = size(Pub2) == constants:pubkey_size(),
            load(Pub2, base64:decode(Priv), Pass),
            unlock(Pass);
        {undefined, undefined, {ok, Pass}} ->
            unlock(Pass);
        _ ->
            ok
    end,
    {noreply, State};
handle_info(_Info, State) ->
    {noreply, State}.
keypair() -> gen_server:call(?MODULE, keypair).
pubkey() -> gen_server:call(?MODULE, pubkey).
sign(M) -> 
    S = status(),
    case S of
	unlocked ->
	    gen_server:call(?MODULE, {sign, M});
	_ -> io:fwrite("you need to unlock your account before you can sign transactions. use keys:unlock(\"password\").\n"),
	     {error, locked}
    end.
raw_sign(M) -> gen_server:call(?MODULE, {raw_sign, M}).
load(Pub, Priv, Brainwallet) when (is_binary(Pub) and is_binary(Priv))-> gen_server:cast(?MODULE, {load, Pub, Priv, Brainwallet}).
unlock(Brainwallet) -> gen_server:cast(?MODULE, {unlock, Brainwallet}).
lock() -> gen_server:cast(?MODULE, lock).
status() -> gen_server:call(?MODULE, status).
change_password(Current, New) -> gen_server:cast(?MODULE, {change_password, Current, New}).
new(Brainwallet) -> gen_server:cast(?MODULE, {new, Brainwallet}).
shared_secret(Pub) -> gen_server:call(?MODULE, {ss, Pub}).
decrypt(EMessage) ->
    packer:unpack(element(3, gen_server:call(?MODULE, {decrypt, EMessage}))).
encrypt(Message, Pubkey) ->
    gen_server:call(?MODULE, {encrypt, packer:pack(Message), Pubkey}).
test() ->
    unlocked = keys:status(),
    Tx = {spend, 1, 1, 2, 1, 1},
    Stx = sign(Tx),
    true = testnet_sign:verify(Stx, 1),
    success.
