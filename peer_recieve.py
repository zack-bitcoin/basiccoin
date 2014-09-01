"""When a peer talks to us, this is how we generate a response. This is the external API.
"""
import networking, custom, tools, blockchain, time
def security_check(dic):
    if 'version' not in dic or dic['version'] != custom.version:
        return {'bool': False, 'error': 'version'}
    else:
        #we could add security features here.
        return {'bool': True, 'newdic': dic}
def blockCount(dic, DB):
    length = DB['length']
    if length >= 0:
        return {'length': length,
                'diffLength': DB['diffLength']}
    else:
        return {'length': -1, 'diffLength': '0'}
def rangeRequest(dic, DB):
    ran = dic['range']
    out = []
    counter = 0
    while (len(tools.package(out)) < custom.max_download
           and ran[0] + counter <= ran[1]):
        block = tools.db_get(ran[0] + counter, DB)
        if 'length' in block:
            out.append(block)
        counter += 1
    return out
def txs(dic, DB):
    return DB['txs']
def pushtx(dic, DB):
    DB['suggested_txs'].put(dic['tx'])
    return 'success'
def pushblock(dic, DB):
    if 'blocks' in dic:
        for block in dic['blocks']:
            DB['suggested_blocks'].put([block, dic['peer']])
    else:
        DB['suggested_blocks'].put([dic['block'], dic['peer']])
    return 'success'
def main(dic, DB):
    funcs = {'blockCount': blockCount, 'rangeRequest': rangeRequest,
             'txs': txs, 'pushtx': pushtx, 'pushblock': pushblock}
    if 'type' not in dic:
        return 'oops: ' +str(dic)
    if dic['type'] not in funcs:
        return ' '.join([dic['type'], 'is not in the api'])
    check = security_check(dic)
    if not check['bool']:
        return check
    try:
        return funcs[dic['type']](check['newdic'], DB)
    except:
        pass
