#!/usr/bin/env python
import random, hashlib, os
from json import dumps as package, loads as unpackage
page_size=50
default_db='000000'
def make_file(f): os.mkdir('db/'+f)
def file_exists(f):
    try:
        os.chdir('db/'+f)
        os.chdir('../..')
        return True
    except:
        return False
def n_to_file(n): return 'h'+n[0:3]+'/'+n[3:]
def raw_write_page(file, txt):
    with open('db/'+file, 'w') as myfile: myfile.write(package(txt))
def write_page(file, txt): 
    file=n_to_file(file)
    if not file_exists(file[0:4]):
        make_file(file[0:4])
    return raw_write_page(file, txt)
def raw_read_page(file):
    try:
        with open('db/'+file, 'r') as myfile: return unpackage(myfile.read())
    except:
        return raw_read_page(file)
def read_page(file):
    file=n_to_file(file)
    return raw_read_page(file)
def key_hash(key): return int(hashlib.md5(key).hexdigest()[0:5], 16)%page_size
def allocate_page(file): write_page(file,  ['n']*page_size)
def get(key, file=default_db):
    key=str(key)
    a=get_raw(key, file)
    if 'page' in a: return get(key, a['page'])
    if 'key' in a and a['key']==key: return a['value']
    else: return 'undefined'
def get_raw(key, file):
    a=read_page(file)[key_hash(key+file)]
    return {'value':'undefined'} if a=='n' else a
def put(key, value, file=default_db, depth=0):
    key=str(key)
    a=read_page(file)
    h=key_hash(key+file)
    old=get_raw(key, file)
    if ('value' in old and old['value']=='undefined') or ('key' in old and old['key']==key):
        a[h]={'value':value, 'key':key}
        write_page(file, a)
    elif 'page' in old:
        return put(key, value, old['page'], depth+1)
    else: #need to create new page recursively
        f=str(random.getrandbits(40))
        allocate_page(f)
        a[h]={'page':f}
        write_page(file, a)
        put(key, value, f)
        put(old['key'], old['value'], f)
    return 'success'
try: os.mkdir('db')
except: pass
f=n_to_file(default_db)
if not file_exists(f[0:4]):
    allocate_page(default_db)

'''
try: 
    with open('db/'+default_db, 'r') as file: pass
except: allocate_page(default_db)
'''

if __name__ == "__main__":
    for i in range(1000):
        put(str(i), str(i))
        print(i)
    for i in range(10):
        print(get(str(i*10)))

