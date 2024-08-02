import logging
import os
import sys
import threading
import typing
from typing import Any

from redis import Redis as r

from config import HOST, PASSWORD, PORT

log = logging.getLogger("telethon")


class Redis(r):

    def __init__(
        self,
        host: str = None,
        port: int = None,
        password: str = None,
        logger=log,
        encoding: str = "utf-8",
        decode_responses=True,
        **kwargs,
    ):
        if ":" in host:
            data = host.split(":")
            host = data[0]
            port = int(data[1])
        if host.startswith("http"):
            logger.error("Your REDIS_URI should not start with http!")
            sys.exit()
        elif not host or not port:
            logger.error("Port Number not found")
            sys.exit()
        kwargs["host"] = host
        if password and len(password) > 1:
            kwargs["password"] = password
        kwargs["port"] = port
        kwargs["encoding"] = encoding
        kwargs["decode_responses"] = decode_responses
        # kwargs['client_name'] = client_name
        # kwargs['username'] = username
        try:
            super().__init__(**kwargs)
        except Exception as e:
            logger.exception(f"Error while connecting to redis: {e}")
            sys.exit()
        self.logger = logger
        self._cache = {}
        threading.Thread(target=self.re_cache).start()

    def re_cache(self):
        key = self.keys()
        for keys in key:
            self._cache[keys] = self.get(keys)
        self.logger.info("Cached {} keys".format(len(self._cache)))

    def get_key(self, key: Any):
        if key in self._cache:
            return self._cache[key]
        else:
            data = self.get(key)
            self._cache[key] = data
            return data

    def del_key(self, key: Any):
        if key in self._cache:
            del self._cache[key]
        return self.delete(key)

    def set_key(self, key: Any = None, value: Any = None):
        self._cache[key] = value
        return self.set(key, value)


db = Redis(
    host=HOST,
    port=PORT,
    password=PASSWORD if len(PASSWORD) > 1 else None,
    decode_responses=True,
)


log.info(f"Starting redis on {HOST}:{PORT}")
if not db.ping():
    log.error(f"Redis is not available on {HOST}:{PORT}")
    exit(1)
