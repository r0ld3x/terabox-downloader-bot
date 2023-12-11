import asyncio
import time

from pyrogram import Client
from telethon.sync import TelegramClient, events

from terabox import get_data, init_download
from tools import download_and_send, get_current_downloading, get_urls_from_string

api_id = 7239207
api_hash = "ed44780dedd182084f2133b16944cf34"

bot = TelegramClient("bot", api_id, api_hash).start(
    bot_token="6447807767:AAEoqvglS00rXAjayIBOH7Mj3N1tAdupgjk"
)
pyrobot = Client(
    "pyro", api_id, api_hash, bot_token="6447807767:AAEoqvglS00rXAjayIBOH7Mj3N1tAdupgjk"
)


@bot.on(events.NewMessage(pattern="/start"))
async def start(m):
    await m.reply(
        "Hello! I am a bot to download videos from terabox. \nJoin @RoldexVerse For Updates. :)"
    )


@bot.on(
    events.NewMessage(
        func=lambda message: message.text and get_urls_from_string(message.text)
    )
)
async def echo_message(m):
    start_code = time.monotonic()
    hm = await m.reply("Sending you the media wait...")
    url = get_urls_from_string(m.text)
    data = get_data(url)
    if data is False:
        return await hm.edit("Sorry!...")
    is_downloading = get_current_downloading(data["file_name"])
    if not is_downloading:
        init_download(data["link"])
    hm = await hm.edit(
        f"Downloading {data['size']}...\nYou can download through the <a href={data['link']}>{data['file_name']}</a>.\nI am also sending you a telegram video of this video.",
        parse_mode="html",
    )

    asyncio.ensure_future(
        download_and_send(
            tgbot=bot,
            pyrobot=pyrobot,
            message=m,
            edit_message=hm,
            file_name=data["file_name"],
            total_size=data["sizebytes"],
        )
    )


pyrobot.run()
bot.run_until_disconnected()
