import asyncio
import time

from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message

from config import api_hash, api_id, bot_token
from terabox import get_data, init_download
from tools import (
    download_and_send,
    get_current_downloading,
    get_urls_from_string,
    is_user_on_chat,
)

bot = Client("pyro", api_id, api_hash, bot_token=bot_token)


@bot.on_message(filters=filters.command("start") & filters.private)
async def start(m: Message):
    await m.reply(
        "Hello! I am a bot to download videos from terabox.\nSend me the terabox link and i will start downloading it. \nJoin @RoldexVerse For Updates. :)",
        reply_to_message_id=m.id,
    )


@bot.on_message(filters.text & filters.private)
async def echo_message(_, m: Message):
    check_if = await is_user_on_chat(bot, -1001345686737, m.from_user.id)
    if not check_if:
        return await m.reply_text(
            "Please join @RoldexVerse then send me the link again.",
            reply_to_message_id=m.id,
        )
    check_if = await is_user_on_chat(bot, -1001320804136, m.from_user.id)
    if not check_if:
        return await m.reply_text(
            "Please join @RoldexVerseChats then send me the link again.",
            reply_to_message_id=m.id,
        )

    url = get_urls_from_string(m.text)
    if not url:
        return await m.reply_text("Please enter a valid url.", reply_to_message_id=m.id)
    hm = await m.reply_text("Sending you the media wait...", reply_to_message_id=m.id)
    data = get_data(url)

    if data is False:
        return await hm.edit("Sorry! API is dead or maybe your link is broken.")
    if data["sizebytes"] > 524288000 and m.chat.id not in [1317173146]:
        return await hm.edit(
            f"Sorry! File is too big. I can download only 500MB and this file is of {data['size']} ."
        )

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
