import pt, custom
from json import dumps as package, loads as unpackage

def pub2addr(pubkey): return pt.pubtoaddr(pubkey)

def sha256(x): return pt.sha256(x)

def sign(msg, privkey): pt.ecdsa_sign(msg, privkey)

def verify(msg, sig, pubkey): return pt.ecdsa_verify(msg, sig, pubkey)

def privtopub(privkey): return pt.privtopub(privkey)

def det_hash(x):#deterministically takes sha256 of dict, list, int, or string

    def det_list(l): return '[%s]' % ','.join(map(det, sorted(l)))
    
    def det_dict(x): 
        list_=map(lambda p: det(p[0]) + ':' + det(p[1]), sorted(x.items()))
        return '{%s}' % ','.join(list_)
        
    def det(x): return {list: det_list, dict: det_dict}.get(type(x), str)(x)
    
    return custom.hash_(det(unpackage(package(x))))
