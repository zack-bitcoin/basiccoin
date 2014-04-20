import json, hashlib
def package(dic): return json.dumps(dic)
def unpackage(dic): return json.loads(dic)
def det_hash(x):
    def sha256(x):
        h=hashlib.sha256()
        h.update(x)
        return h.hexdigest()
    def det_list(l):
        out=''
        for i in l:
            out+=det(i)+','
        return '['+out+']'
    def det_dic(dic):
        out=''
        for i in dic.keys():
            out+=det(i)+':'+det(dic[i])+','
        return '{'+out+'}'
    funcs={str(type('string')):str, str(type(u'unicode')):str, str(type(27)):str, str(type(1.1)):str, str(type([1,2,3])):det_list, str(type({'a':1})):det_dic}
    def det(x): return funcs[str(type(x))](x)
    return sha256(det(x))
