import asyncio
import os
import time
from uuid import uuid4
from typing import Optional, List

import redis
import telethon
from telethon import TelegramClient, events
from telethon.tl.functions.messages import ForwardMessagesRequest
from telethon.types import Message, UpdateNewMessage

from cansend import CanSend
from config import API_ID, API_HASH, BOT_TOKEN, HOST, PORT, PASSWORD, PRIVATE_CHAT_ID, ADMINS
from terabox import get_data
from tools import (
    convert_seconds,
    download_file,
    download_image_to_bytesio,
    extract_code_from_url,
    get_formatted_size,
    get_urls_from_string,
    is_user_on_chat,
)

bot = TelegramClient("tele", API_ID, API_HASH)

db = redis.Redis(
    host=HOST,
    port=PORT,
    password=PASSWORD,
    decode_responses=True,
)

async def check_user_joined_channels(user_id: int) -> bool:
    channels = ["@RoldexVerse", "@RoldexVerseChats"]
    for channel in channels:
        if not await is_user_on_chat(bot, channel, user_id):
            return False
    return True

@bot.on(events.NewMessage(pattern="/start$", func=lambda x: x.is_private))
async def start(event: UpdateNewMessage) -> None:
    if not await check_user_joined_channels(event.peer_id):
        await event.reply("Please join @RoldexVerse and @RoldexVerseChats then send me the link again.")
        return

    reply_text = """
Hello! I am a bot to download videos from terabox.
Send me the terabox link and I will start downloading it.
Join @RoldexVerse For Updates
[Source Code](https://github.com/r0ld3x/terabox-downloader-bot)
"""
    await event.reply(reply_text, link_preview=False, parse_mode="markdown")

@bot.on(events.NewMessage(pattern="/start (.*)", func=lambda x: x.is_private))
async def start_with_args(event: UpdateNewMessage) -> None:
    if not await check_user_joined_channels(event.peer_id):
        await event.reply("Please join @RoldexVerse and @RoldexVerseChats then send me the link again.")
        return

    text = event.pattern_match.group(1)
    file_id = db.get(str(text))
    if file_id:
        await bot(
            ForwardMessagesRequest(
                from_peer=PRIVATE_CHAT_ID,
                id=[int(file_id)],
                to_peer=event.chat.id,
                drop_author=True,
                background=True,
                drop_media_captions=False,
                with_my_score=True,
            )
        )

@bot.on(events.NewMessage(pattern="/remove (.*)", from_users=ADMINS))
async def remove(event: UpdateNewMessage) -> None:
    user_id = event.pattern_match.group(1)
    if db.get(f"check_{user_id}"):
        db.delete(f"check_{user_id}")
        await event.reply(f"Removed {user_id} from the list.")
    else:
        await event.reply(f"{user_id} is not in the list.")

@bot.on(events.NewMessage(func=lambda message: message.text and get_urls_from_string(message.text) and message.is_private))
async def get_message(event: Message) -> None:
    asyncio.create_task(handle_message(event))

async def handle_message(event: Message) -> None:
    url = get_urls_from_string(event.text)
    if not url:
        await event.reply("Please enter a valid url.")
        return

    if not await check_user_joined_channels(event.peer_id):
        await event.reply("Please join @RoldexVerse and @RoldexVerseChats then send me the link again.")
        return

    if db.get(event.sender_id) and event.sender_id not in [1317173146]:
        await event.reply("You are spamming. Please wait 1 minute and try again.")
        return

    hm = await event.reply("Sending you the media wait...")
    count = db.get(f"check_{event.sender_id}")
    if count and int(count) > 5:
        await hm.edit("You are limited now. Please come back after 2 hours or use another account.")
        return

    shorturl = extract_code_from_url(url)
    if not shorturl:
        await hm.edit("Seems like your link is invalid.")
        return

    file_id = db.get(shorturl)
    if file_id:
        await send_existing_file(event, hm, file_id)
        return

    data = get_data(url)
    if not data:
        await hm.edit("Sorry! API is dead or maybe your link is broken.")
        return

    db.set(event.sender_id, time.monotonic(), ex=60)

    if not is_supported_file(data['file_name']):
        await hm.edit("Sorry! File is not supported. I can download only .mp4, .mkv and .webm files.")
        return

    if int(data["sizebytes"]) > 524288000 and event.sender_id not in [1317173146]:
        await hm.edit(f"Sorry! File is too big. I can download only 500MB and this file is of {data['size']}.")
        return

    await process_and_send_file(event, hm, data)

async def send_existing_file(event: Message, hm: Message, file_id: str) -> None:
    try:
        await hm.delete()
    except Exception:
        pass

    await bot(
        ForwardMessagesRequest(
            from_peer=PRIVATE_CHAT_ID,
            id=[int(file_id)],
            to_peer=event.chat.id,
            drop_author=True,
            background=True,
            drop_media_captions=False,
            with_my_score=True,
        )
    )
    db.set(event.sender_id, time.monotonic(), ex=60)
    update_user_count(event.sender_id)

def is_supported_file(filename: str) -> bool:
    return filename.lower().endswith(('.mp4', '.mkv', '.webm'))

async def process_and_send_file(event: Message, hm: Message, data: dict) -> None:
    start_time = time.time()
    cansend = CanSend()
    uuid = str(uuid4())
    thumbnail = download_image_to_bytesio(data["thumb"], "thumbnail.png")

    async def progress_bar(current_downloaded: int, total_downloaded: int, state: str = "Sending") -> None:
        if not cansend.can_send():
            return

        bar_length = 20
        percent = current_downloaded / total_downloaded
        arrow = "█" * int(percent * bar_length)
        spaces = "░" * (bar_length - len(arrow))

        elapsed_time = time.time() - start_time
        upload_speed = current_downloaded / elapsed_time if elapsed_time > 0 else 0
        time_remaining = (total_downloaded - current_downloaded) / upload_speed if upload_speed > 0 else 0

        progress_text = f"{state} `{data['file_name']}`\n"
        progress_text += f"[{arrow + spaces}] {percent:.2%}\n"
        progress_text += f"Speed: **{get_formatted_size(upload_speed)}/s**\n"
        progress_text += f"Time Remaining: `{convert_seconds(time_remaining)}`\n"
        progress_text += f"Size: **{get_formatted_size(current_downloaded)}** / **{get_formatted_size(total_downloaded)}**"

        await hm.edit(progress_text, parse_mode="markdown")

    try:
        file = await send_file_to_chat(data, thumbnail, uuid, progress_bar)
    except telethon.errors.rpcerrorlist.WebpageCurlFailedError:
        file = await download_and_send_file(data, thumbnail, uuid, progress_bar)
    except Exception:
        await hm.edit(f"Sorry! Download Failed but you can download it from [here]({data['direct_link']}).", parse_mode="markdown")
        return

    if file:
        await forward_file_to_user(event, file, hm)
        update_database(event.sender_id, shorturl, uuid, file.id)

async def send_file_to_chat(data: dict, thumbnail: Optional[bytes], uuid: str, progress_callback) -> Message:
    return await bot.send_file(
        PRIVATE_CHAT_ID,
        file=data["direct_link"],
        thumb=thumbnail,
        progress_callback=progress_callback,
        caption=get_file_caption(data, uuid),
        supports_streaming=True,
        spoiler=True,
    )

async def download_and_send_file(data: dict, thumbnail: Optional[bytes], uuid: str, progress_callback) -> Optional[Message]:
    download = await download_file(data["direct_link"], data["file_name"], progress_callback)
    if not download:
        return None

    file = await bot.send_file(
        PRIVATE_CHAT_ID,
        download,
        caption=get_file_caption(data, uuid),
        progress_callback=progress_callback,
        thumb=thumbnail,
        supports_streaming=True,
        spoiler=True,
    )

    try:
        os.unlink(download)
    except Exception as e:
        print(f"Error deleting file: {e}")

    return file

def get_file_caption(data: dict, uuid: str) -> str:
    return f"""
File Name: `{data['file_name']}`
Size: **{data["size"]}** 
Direct Link: [Click Here](https://t.me/teraboxdown_bot?start={uuid})

@RoldexVerse
"""

async def forward_file_to_user(event: Message, file: Message, hm: Message) -> None:
    try:
        await hm.delete()
    except Exception as e:
        print(f"Error deleting message: {e}")

    await bot(
        ForwardMessagesRequest(
            from_peer=PRIVATE_CHAT_ID,
            id=[file.id],
            to_peer=event.chat.id,
            top_msg_id=event.id,
            drop_author=True,
            background=True,
            drop_media_captions=False,
            with_my_score=True,
        )
    )

def update_database(sender_id: int, shorturl: str, uuid: str, file_id: int) -> None:
    if shorturl:
        db.set(shorturl, file_id)
    db.set(uuid, file_id)
    db.set(sender_id, time.monotonic(), ex=60)
    update_user_count(sender_id)

def update_user_count(sender_id: int) -> None:
    count = db.get(f"check_{sender_id}")
    db.set(
        f"check_{sender_id}",
        int(count) + 1 if count else 1,
        ex=7200,
    )

if __name__ == "__main__":
    bot.start(bot_token=BOT_TOKEN)
    bot.run_until_disconnected()
