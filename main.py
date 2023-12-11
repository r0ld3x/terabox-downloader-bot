import asyncio
import time

from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message

from config import api_hash, api_id, bot_token
from terabox import get_data, init_download
from tools import download_and_send, get_current_downloading, get_urls_from_string

bot = Client("pyro", api_id, api_hash, bot_token=bot_token)


@bot.on_message(filters=filters.command("start") & filters.private)
async def start(m):
    await m.reply(
        "Hello! I am a bot to download videos from terabox. \nJoin @RoldexVerse For Updates. :)"
    )


@bot.on_message(filters.text & filters.private)
async def echo_message(_, m: Message):
    url = get_urls_from_string(m.text)
    if not url:
        return await m.reply_text("Please enter a valid url.", reply_to_message_id=m.id)
    hm = await m.reply_text("Sending you the media wait...", reply_to_message_id=m.id)
    data = get_data(url)
    if data is False:
        return await hm.edit("Sorry!...")
    is_downloading = get_current_downloading(data["file_name"])
    if not is_downloading:
        init_download(data["link"])
    hm = await hm.edit(
        f"Downloading {data['size']}...\nYou can download through the <a href={data['link']}>{data['file_name']}</a>.\nI am also sending you a telegram video of this video.",
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )

    asyncio.ensure_future(
        download_and_send(bot, m, hm, data["file_name"], data["sizebytes"])
    )


bot.run()
