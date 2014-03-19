import blockchain, settings, threading, gui, listener, os, subprocess, re
import pybitcointools as pt
my_privkey=pt.sha256(settings.brain_wallet)
my_pubkey=pt.privtopub(my_privkey)

def kill_processes_using_ports(ports):
    popen = subprocess.Popen(['netstat', '-lpn'],
                             shell=False,
                             stdout=subprocess.PIPE)
    (data, err) = popen.communicate()
    pattern = "^tcp.*((?:{0})).* (?P<pid>[0-9]*)/.*$"
    pattern = pattern.format(')|(?:'.join(ports))
    prog = re.compile(pattern)
    for line in data.split('\n'):
        match = re.match(prog, line)
        if match:
            pid = match.group('pid')
            subprocess.Popen(['kill', '-9', pid])
try:
    kill_processes_using_ports([str(settings.listen_port), str(settings.gui_port)])
    kill_processes_using_ports([str(settings.listen_port), str(settings.gui_port)])
except:
    #so windows doesn't die
    pass
if __name__ == '__main__':
    #the first miner is for finding blocks. the second miner is for playing go and for talking to the network.
    todo=[[blockchain.mine, 
           (my_pubkey, ['http://localhost:'+str(settings.listen_port)+'/info?{}'], settings.hashes_till_check, '_miner')],
          [listener.main, (settings.listen_port, )],
          [blockchain.mine, (my_pubkey, settings.peers_list, 0)],
          [gui.main, (settings.gui_port, settings.brain_wallet)]
          ]
    for i in todo:
        t = threading.Thread(target=i[0], args = i[1])
#        t.daemon = True
        t.start()

