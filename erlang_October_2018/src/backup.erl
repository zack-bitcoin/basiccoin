-module(backup).
-export([read/2, read_size/1]).

-define(backup, "backup/").

-define(word, constants:word_size()).
read_size(File) ->
    filelib:file_size(?backup++File) div ?word.
read(File, N) ->
    {ok, RFile } = file:open(?backup++File, [read, binary, raw]),
    {ok, Out} = file:pread(RFile, N*?word, ?word),
    file:close(RFile),
    Out.
