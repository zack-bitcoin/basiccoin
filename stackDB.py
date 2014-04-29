import json
#This is unnecessary because queues do the same thing. Queues are superior because the info could stay in ram.
#https://docs.python.org/2/library/queue.html
def load(file):
    def line2dic(line):
        return json.loads(line.strip('\n'))
    out=[]
    try:
        with open(file, 'rb') as myfile:
            a=myfile.readlines()
            for i in a:
                #                if i.__contains__('"'):
                out.append(line2dic(i))
    except:
        pass
    return out
def push(file, x):
    with open(file, 'a') as myfile:
        myfile.write(json.dumps(x)+'\n')
def reset(file): return open(file, 'w').close()
def put(file, dic):
    reset(file)
    push(file, dic)
def set_hash(x): return put('recentHash.db', x)
def current_hash(x): 
    try:
        return load('recentHash.db')[0]
    except:
        return 0
def set_length(x): return put('length.db', x)
def current_length(): 
    try:
        return load('length.db')[0]
    except:
        return -1
def set_sig_length(x): return put('sig_length.db', x)#number of juror signatures
def current_sig_length(): 
    try:
        return load('sig_length.db')[0]
    except:
        return -1
def add_tx(tx): return push('txs.db', tx)
def current_txs(): 
    try:
        return load('txs.db')
    except:
        return []
def reset_txs(): return reset('txs.db')
