import cPickle
state_db='state.db'
backup_db='backup_states.db'
empty_state={'length':0, 'recent_hash':'00000000000'}
def fs_save(database, dic):
    cPickle.dump(dic, open(database, 'wb'))
def fs_load(database, sort=[]):
    try:
        out=cPickle.load(open(database, 'rb'))
        return out
    except:
        fs_save(database, sort)#these are list-databases
        return cPickle.load(open(database, 'rb'))      
def ex(db_extention, db):
    return db.replace('.db', db_extention+'.db')
def save_state(state, db_extention=""):#state contains the positions of every board, and who has how much money.
    return fs_save(ex(db_extention, state_db), state)
def current_state(db_extention=""):
    return fs_load(ex(db_extention, state_db), empty_state)
def backup_state(state, db_extention=''):
    backups=fs_load(ex(db_extention, backup_db), [])
    backups.append(state)
    fs_save(ex(db_extention, backup_db), backups)
def recent_backup(db_extention=''):#This deletes the backup that it uses.
    backups=fs_load(ex(db_extention,backup_db), [])
    try:
        fs_save(ex(db_extention, backup_db), backups[:-1])
        return backups[-1]
    except:
        return empty_state

