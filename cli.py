#!/usr/bin/env python
import networking, sys, tools, custom, os, multiprocessing, threads, api, blockchain

def daemonize(f):
    if sys.platform == 'win32':
        pypath = list(os.path.split(sys.executable))
        pypath[-1] = 'pythonw.exe'
        os.system('start '+os.path.join(*pypath)+' threads.py '+p)
        sys.exit(0)
    pid=os.fork()
    if pid==0: f()
    else: sys.exit(0)
def get_address(tx):
    pubkey=str(raw_input('What is your address or pubkey\n>'))
    if len(pubkey)>40:
        out=tools.make_address([pubkey], 1)
    else:
        out=pubkey    
    return tx
def main(c=0):
    if type(c)==int:
        p={'command':sys.argv[1:]}
    else:
        p={'command':c}
    if len(p['command'])==0:
        p['command'].append(' ')
    c=p['command']
    if c[0]=='make_PM':
        tx=build_pm()
        return run_command({'command':['pushtx', tools.package(tx).encode('base64')]})
    elif c[0]=='buy_shares':
        tx=build_buy_shares()
        return run_command({'command':['pushtx', tools.package(tx).encode('base64')]})
    elif c[0]=='start':
        r=connect({'command':'blockcount'})
        if is_off(r):
            p=raw_input('what is your password?\n')
            daemonize(lambda: threads.main(p))
        else:
            print('blockchain is already running')
    elif c[0]=='new_address':
        if len(c)<2:
            print('what is your brain wallet? not enough inputs.')
        else:
            privkey=tools.det_hash(c[1])
            pubkey=tools.privtopub(privkey)
            address=tools.make_address([pubkey], 1)
            return({'brain':str(c[1]),
                    'privkey':str(privkey),
                    'pubkey':str(pubkey),
                    'address':str(address)})
    else:
        return run_command(p)
def connect(p):
    peer=['localhost', custom.api_port]
    response=networking.send_command(peer, p, 5)
    if tools.can_unpack(response):
        response=tools.unpackage(response)
    return response
def is_off(response): return type(response)==type({'a':1}) and 'error' in response
def run_command(p):
    response=connect(p)
    if is_off(response):
        print('blockchain is probably off. Use command: "./cli.py start" to turn it on.')
    return response

if __name__=='__main__':
    print(main())

