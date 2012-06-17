import cPickle as pickle
from uuid import uuid4
import time

class RedisSessionStore:

    def __init__(self, redis_connection, **options):
        self.options = {
            'key_prefix': 'session',
            'expire': 30,
        }
        self.options.update(options)
        self.redis = redis_connection

    def prefixed(self, sid):
        return '%s:%s' % (self.options['key_prefix'], sid)

    def generate_sid(self):
        print "generated new sid"
        return uuid4().get_hex()

    def get_session(self, sid, name):
        data = self.redis.hget(self.prefixed(sid), name)
        session = pickle.loads(data) if data else dict()
        return session

    def set_session(self, sid, name, session_data):
        expiry = self.options['expire']
        self.redis.hset(self.prefixed(sid), name, pickle.dumps(session_data))
        if expiry:
            self.redis.expire(self.prefixed(sid), expiry)

    def delete_session(self, sid):
        self.redis.delete(self.prefixed(sid))

class Session:

    def __init__(self, session_store, sessionid=None):
        self._store = session_store
        self._sessionid = sessionid if sessionid else self._store.generate_sid()

    def clear(self):
        self._store.delete_session(self._sessionid)

    def access(self, remote_ip):
        access_info = {'remote_ip':remote_ip, 'time':'%.6f' % time.time()}
        self._store.set_session(
                self._sessionid,
                'last_access',
                pickle.dumps(access_info)
                )

    def last_access(self):
        access_info = self._store.get_session(self._sessionid, 'last_access')
        return pickle.loads(access_info)

    def fetch(self, key):
        return self._store.get_session(self._sessionid, key)

    def update(self, key, value):
        return self._store.set_session(self._sessionid, key, value)

    def uploaded(self):
        val = self._store.get_session(self._sessionid, 'uploaded')
        return val if val else []

    def setUploaded(self, value):
        return self._store.set_session(self._sessionid, 'uploaded', value)
        
    @property
    def sessionid(self):
        return self._sessionid

    def save(self):
        self._store.set_session(self._sessionid)
