import json
def load(file):#keep
    def line2dic(line):
        return json.loads(line.strip('\n'))
    out=[]
    try:
        with open(file, 'rb') as myfile:
            a=myfile.readlines()
            for i in a:
                out.append(line2dic(i))
    except:
        pass
    return out
def push(file, x):#keep
    with open(file, 'a') as myfile:
        myfile.write(json.dumps(x)+'\n')
def reset(file): return open(file, 'w').close()#keep
