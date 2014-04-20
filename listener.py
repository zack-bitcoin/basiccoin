import networking, custom, stackDB
#every message needs to be smaller than 55,000 letters, but blocks need to be bigger than that.
#to make it simple, first version requires txs to be smaller than 55,000

#it is bad that this file imports "blockchain". We cannot do that. We need to create some stackDB to hold necessary information.
def main(dic):
    def security_check(dic):
        if 'version' not in dic or dic['version']!=custom.version:
            return {'bool':False, 'error':'version'}
        else:
            #we could add security freatures here.
            return {'bool':True, 'newdic':dic}
    def blockCount(dic):    
        length=stackDB.current_length()
        if length>0:
            return {'length':length, 'prevHash':stackDB.load('recentHash.db')[0]}#blockchain.db_get(length)['prevHash']}
        else:
            return {'length':0, 'prevHash':0}
    def rangeRequest(dic):
        ran=dic['range']
        if ran[0]==0:
            ran[0]=1
        out=[]
        counter=0
        while len(package(out))<50000 and ran[0]+counter<=ran[1]:
            counter+=1
            out.append(blockchain.db_get(ran[0]+counter))
        return out
    def txs(dic): return stackDB.current_txs()
    def pushtx(dic): 
        stackDB.push('suggested_txs.db', dic['tx'])
        return 'success'
    def pushchain(dic):
        stackDB.push('suggested_blocks.db', dic['block'])
        return 'success'
    funcs={'blockCount':blockCount, 'rangeRequest':rangeRequest, 'txs':txs, 'pushtx':pushtx, 'pushchain':pushchain}
    if dic['type'] not in funcs.keys():
        return str(dic['type'])+' is not in the api'
    check=security_check(dic)
    if not check['bool']:
        return check
    return funcs[dic['type']](check['newdic'])
def server(): return networking.serve_forever(main, custom.listen_port)

