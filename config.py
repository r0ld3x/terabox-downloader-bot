import os
from os import getenv

API_ID =   # api id
API_HASH = ""  # api hash

BOT_TOKEN = ""  # bot token


## REDIS
HOST = ""  # redis host uri
PORT = 6379  # redis port
PASSWORD = ""  # redis password

PRIVATE_CHAT_ID = -1001234567890  # CHAT WHERE YOU WANT TO STORE VIDEOS
COOKIE = os.getenv("COOKIE", None)  # COOKIE FOR AUTHENTICATION (get from chrome dev tools) ex: "PANWEB=1; csrfToken=; lang=en; TSID=; __bid_n=; _ga=; __stripe_mid=; ndus=; browserid==; ndut_fmt=; _ga_06ZNKL8C2E=" (dont use this)
ADMINS = [1317173146]
