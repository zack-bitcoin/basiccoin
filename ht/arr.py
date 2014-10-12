import ht, os, sys
from json import dumps as package, loads as unpackage
def buffer_(str_to_pad, size):
    return str_to_pad.rjust(size, '0')
def last():#this discovers where the end of the list is.
    i=0
    out=0
    while True:
        if ht.file_exists(str(i)):
            j=1
            while True:
                if ht.file_exists(str(i)+'/a'+str(i*1000+j)):
                    out=i*1000+j
                else:
                    #print('file did not exist: db/'+str(i)+'/a'+str(i*1000+j))
                    return out
                j+=1
        else:
            #print('file did not exist: db/'+str(i))
            return out
        i+=1
DB={'last':last()}
#print('DB: ' +str(DB))
def append(x):
    DB['last']+=1
    f=str(DB['last']/1000)
    if not ht.file_exists(f):
        ht.make_file(f)
    ht.raw_write_page(f+'/a'+str(DB['last']), x)
    return DB['last']
def lookup(n):
    f=str(n/1000)
    return ht.raw_read_page(f+'/a'+str(n))
def replace(n, x):
    f=str(n/1000)
    if not ht.file_exists(f):
        return {'error':'n is too big'}
    ht.raw_write_page(f+'/a'+str(n), x)


if __name__ == "__main__":
    for i in range(3000):
        append(str(i)*100)
    print(lookup(999))
    replace(999, 'abc')
    print(lookup(999))
