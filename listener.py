import networking, custom, stackDB, tools, leveldb, shutil, time, blockchain
#every message needs to be smaller than 55,000 letters, but blocks need to be bigger than that.
#to make it simple, first version requires txs to be smaller than 55,000

#it is bad that this file imports "blockchain". We cannot do that. We need to create some stackDB to hold necessary information.
def main(dic, DB):
    def security_check(dic):
        if 'version' not in dic or dic['version']!=custom.version:
            return {'bool':False, 'error':'version'}
        else:
            #we could add security freatures here.
            return {'bool':True, 'newdic':dic}
    def blockCount(dic, DB):
        length=stackDB.current_length()
        if length>0:
            return {'length':length, 'prevHash':stackDB.load('recentHash.db')[0], 'sig_length':0}#blockchain.db_get('sig_length', DB)}
        else:
            return {'length':0, 'prevHash':0, 'sig_length':0}
    def rangeRequest(dic, DB):
        print('Range Request: '+str(dic))
        ran=dic['range']
        out=[]
        counter=0
        while len(tools.package(out))<50000 and ran[0]+counter<=ran[1]:
            block=blockchain.db_get(ran[0]+counter, DB)
            if 'length' in block:
                out.append(block)
            counter+=1
        return out
    def txs(dic, DB): return stackDB.current_txs()
    def pushtx(dic, DB): 
        print('PUSHTX')
        stackDB.push('suggested_txs.db', dic['tx'])
        return 'success'
    def pushblock(dic, DB):
        #print('PUSHBLOCK')
        stackDB.push('suggested_blocks.db', dic['block'])
        return 'success'
    funcs={'blockCount':blockCount, 'rangeRequest':rangeRequest, 'txs':txs, 'pushtx':pushtx, 'pushblock':pushblock}
    if dic['type'] not in funcs.keys():
        return str(dic['type'])+' is not in the api'
        #print('got info: ' +str(dic))
    check=security_check(dic)
    if not check['bool']:
        return check
    return funcs[dic['type']](check['newdic'], DB)
def server(DB): return networking.serve_forever(main, custom.listen_port, DB)

