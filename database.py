from multiprocessing import Process
import os
import json

def default_entry(): return dict(count=0, amount=0)

def _noop():
    return None

class DatabaseProcess(Process):
    '''
    Manages operations on the database.
    '''
    def __init__(self, heart_queue, database_name, logf, port):
        super(DatabaseProcess, self).__init__(name='database')
        self.heart_queue = heart_queue
        self.database_name = database_name
        self.logf = logf
        self.port = port

    def get(self, args):
        '''Gets the key in args[0] using the salt'''
        try:
            return json.loads(self._get(self.salt + str(args[0])))
        except KeyError:
            return default_entry()

    def put(self, args):
        '''
        Puts the val in args[1] under the key in args[0] with the salt
        prepended to the key.
        '''
        self._put(self.salt + str(args[0]), json.dumps(args[1]))

    def existence(self, args):
        '''
        Checks if the key in args[0] with the salt prepended is
        in the database.
        '''
        try:
            self._get(self.salt + str(args[0]))
        except KeyError:
            return False
        else:
            return True

    def delete(self, args):
        '''
        Removes the entry in the database under the the key in args[0]
        with the salt prepended.
        '''
        # It isn't an error to try to delete something that isn't there.
        try:
            self._del(self.salt + str(args[0]))
        except:
            pass

    def run(self):
        import networking
        import sys
        if sys.platform == 'win32':
            import bsddb
            self.DB = bsddb.hashopen(self.database_name)
            self._get = self.DB.__getitem__
            self._put = self.DB.__setitem__
            self._del = self.DB.__delitem__
            self._close = self.DB.close
        else:
            import leveldb
            self.DB = leveldb.LevelDB(self.database_name)
            self._get = self.DB.Get
            self._put = self.DB.Put
            self._del = self.DB.Delete
            self._close = _noop # leveldb doesn't have a close func
        try:
            self.salt = self._get('salt')
        except KeyError:
            self.salt = os.urandom(5)
            self._put('salt', self.salt)
        def command_handler(command):
            try:
                name = command['type']
                assert (name not in ['__init__', 'run'])
                return getattr(self, name)(command['args'])
            except Exception as exc:
                self.logf(exc)
                self.logf('command: ' + str(command))
                self.logf('command type: ' + str(type(command)))
                return {'error':'bad data'}
        networking.serve_forever(command_handler, self.port, self.heart_queue)
        self._close()
