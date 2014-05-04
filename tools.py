import hashlib
from json import dumps as package, loads as unpackage
def det_hash(x):#deterministically hash
    def det(x): return {list: (lambda l: '[%s]' % ','.join(map(det, sorted(l)))),
                        dict:(lambda x: '{%s}' % ','.join(map(lambda p: det(p[0]) + ':' + det(p[1]), sorted(x.items()))))}.get(type(x), str)(x)
    return hashlib.sha256(det(unpackage(package(x)))).hexdigest()
