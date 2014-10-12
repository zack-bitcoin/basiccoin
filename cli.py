#!/usr/bin/env python
import networking, sys, tools, custom, os, multiprocessing, threads

def daemonize(f):
    pid=os.fork()
    if pid==0: f()
    else: sys.exit(0)
def main():
    info=sys.argv
    p={'command':sys.argv[1:]}
    if len(p['command'])==0:
        p['command'].append(' ')
    c=p['command']
    if c[0]=='start':
        r=connect({'command':'blockcount'})
        if is_truthcoin_off(r):
            p=raw_input('what is your password?\n')
            daemonize(lambda: threads.main(p))
        else:
            print('truthcoin is already running')
    elif c[0]=='new_address':
        if len(c)<2:
            print('what is your brain wallet? not enough inputs.')
        else:
            privkey=tools.det_hash(c[1])
            pubkey=tools.privtopub(privkey)
            address=tools.make_address([pubkey], 1)
            print('brain: ' +str(c[1]))
            print('privkey: ' +str(privkey))
            print('pubkey: ' +str(pubkey))
            print('address: ' +str(address))
    else:
        run_command(p)
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
        print('response was: ' +str(response))
        print('is probably off. Use command: "./cli.py start" to turn it on.')
    else:
        print(response)

main()

