<h1 align="center" id="title">Terabox Downloader Bot</h1>

<p align="center"><img src="https://socialify.git.ci/r0ld3x/terabox-downloader-bot/image?description=1&descriptionEditable=A%20high%20level%20telegram%20bot%20written%20in%20Python%20for%20downloading%20files%20from%20Terabox%20using%20the%20Terabox%20API%20&font=Jost&forks=1&issues=1&language=1&name=1&owner=1&pattern=Overlapping%20Hexagons&pulls=1&stargazers=1&theme=Auto" alt="project-image"></p>

### A telegram bot for downloading terabox videos fastly

## Features:

- Stop downloading
- Token system
- Token Regenration after 1 hour
- 1 minute anti spam
- Download videos fastly
- Fast
- Easy to update

## **Table of Contents**

1.  Getting Started
2.  Installation Steps
3.  Commands
4.  Admins Commands
5.  🍰 Guidelines

## **Getting Started**

To get started with the bot, you'll need to install the required dependencies and configure the bot with your own API credentials.

## Dependencies

- Python 3.11
- <a href="https://github.com/LonamiWebs/Telethon">telethon</a> library
- Redis

## 🛠️ Installation Steps:

<p>1. <a href="https://www.python.org/downloads/">Download latest version of python</a></p>
<p>2. <a href="https://github.com/r0ld3x/terabox-downloader-bot/archive/refs/heads/main.zip">Download this repo</a></p>

<p>3. Unzip and open terminal in that folder</p>

<p>4. Download requirement's</p>

```
pip install -r requirements.txt
```

<p>5. Open config.py and fill it</p>

```python
API_ID = 123456  # api id
API_HASH = "ABC-DEF1234ghIkl-zyx57W2v1u123ew11"  # api hash

BOT_TOKEN = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"  # bot token


## REDIS
HOST = "localhost"  # redis host uri
PORT = 6379  # redis port
PASSWORD = ""  # redis password

PRIVATE_CHAT_ID = -1001234567890  # CHAT WHERE YOU WANT TO STORE VIDEOS
COOKIE = ""  # COOKIE FOR AUTHENTICATION (get from chrome dev tools) ex: "PANWEB=1; csrfToken=;
ADMINS = [1317173146]


BOT_USERNAME = "teraboxdown_bot"

# Force user to join this channel. (make sure you have promoted the bot on this chat.)
FORCE_LINK = "@RoldexVerse"

PUBLIC_EARN_API = ""  # https://publicearn.com/api


```

### Get terabox cookie:

1. Login in terabox with premium account
2. Open any terabox link and watch the video below

https://github.com/r0ld3x/terabox-downloader-bot/assets/77254818/1b68e6ae-715f-4778-845e-4b696762ea93

<p>6. start the bot</p>

```
python main.py
```

```
python bot.py
```
## **Commands**

The bot's commands are defined in `bot.py` and `main.py`. The available commands are:

- `/start`: Start the bot
- `/gen`: Generate api
- Send a link to start downloading it.

## **Admins Commands**

The admin bot's commands are defined in `bot.py`. The available commands are:

- `/remove`:
- `/removeall`: Remove all downloaded videos which are saved in local

## 🍰 Guidelines:

Use at own risk. I am not responsible for break of any Terms and conditions of any companies and businesses.
