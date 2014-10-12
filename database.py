import networking, copy, custom, ht
def main(heart_queue):
    def responder(command):
        if type(command)!=dict or 'type' not in command:
            tools.log('database main command: ' +str(command))
            tools.log('database main command: ' +str(type(command)))
            return {'error': 'bad data'}
        else:
            return dbfunc[command['type']](command['args'])
    return networking.serve_forever(responder, custom.database_port, heart_queue)


def putCommand(args): return db_put(args[0], args[1])
def getCommand(args): return db_get(args[0])
def exiCommand(args): return db_existence(args[0])
def delCommand(args): return db_delete(args[0])
default_entry={'count': 0, 'amount': 0, 'votecoin':{}, 'votes':{}, 'shares':{}}
def db_get(n, DB={}):
    out=ht.get(n)
    if out=='undefined':
        return copy.deepcopy(default_entry)
    return out
def db_put(key, dic, DB={}): 
    return ht.put(key, dic)
def db_delete(key, DB={}): return db_put(key, 'n', DB)
def db_existence(key, DB={}):
    n=str(key)
    out=ht.get(n)
    return not out=='undefined'

dbfunc={'put':putCommand, 'get':getCommand, 'existence':exiCommand, 'delete':delCommand}

if __name__ == "__main__":
    import Queue
    main(Queue.Queue())
