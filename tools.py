import json, hashlib
def package(dic):return json.dumps(dic)
def unpackage(dic):return json.loads(dic)
def det_hash(x):
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
    def det(x):return {list:det_list, dict:det_dic}.get(type(x), str)(x)
    def sha256(x):return hashlib.sha256(x).hexdigest()
    return sha256(det(x))

