import logging
import time

import humanreadable as hr
from telethon import Button
from telethon.sync import TelegramClient, events
from telethon.tl.custom.message import Message
from telethon.types import UpdateNewMessage

from config import (ADMINS, API_HASH, API_ID, BOT_TOKEN, BOT_USERNAME,
                    FORCE_LINK)
from redis_db import db
from send_media import VideoSender
from tools import generate_shortenedUrl, is_user_on_chat, remove_all_videos

log = logging.getLogger(__name__)

bot = TelegramClient("bot", API_ID, API_HASH)


@bot.on(
    events.NewMessage(
        pattern="/start$",
        incoming=True,
        outgoing=False,
        func=lambda x: x.is_private,
    )
)
async def start(m: Message):
    reply_text = """
Hello there! I'm your friendly video downloader bot specially designed to fetch videos from Terabox. Share the Terabox link with me, and I'll swiftly get started on downloading it for you.

Let's make your video experience even better!
"""
    await m.reply(
        reply_text,
        link_preview=False,
        parse_mode="markdown",
        buttons=[
            [
                Button.url(
                    "Website Source Code", url="https://github.com/r0ld3x/terabox-app"
                ),
                Button.url(
                    "Bot Source Code",
                    url="https://github.com/r0ld3x/terabox-downloader-bot",
                ),
            ],
            [
                Button.url("Channel ", url="https://t.me/RoldexVerse"),
                Button.url("Group ", url="https://t.me/RoldexVerseChats"),
            ],
        ],
    )


@bot.on(
    events.NewMessage(
        pattern="/gen$",
        incoming=True,
        outgoing=False,
        func=lambda x: x.is_private,
    )
)
async def generate_token(m: Message):
    is_user_active = db.get(f"active_{m.sender_id}")
    if is_user_active:
        ttl = db.ttl(f"active_{m.sender_id}")
        t = hr.Time(str(ttl), default_unit=hr.Time.Unit.SECOND)
        return await m.reply(
            f"""You are already active.
Your session will expire in {t.to_humanreadable()}."""
        )
    shortenedUrl = generate_shortenedUrl(m.sender_id)
    if not shortenedUrl:
        return await m.reply("Something went wrong. Please try again.")
    # if_token_avl = db.get(f"token_{m.sender_id}")
    # if not if_token_avl:
    # else:
    #     uid, shortenedUrl = if_token_avl.split("|")
    text = f"""
Hey {m.sender.first_name or m.sender.username}!

It seems like your Ads token has expired. Please refresh your token and try again.

Token Timeout: 1 hour

What is a token?
This is an Ads token. After viewing 1 ad, you can utilize the bot for the next 1 hour.

Keep the interactions going smoothly! 😊
"""

    await m.reply(
        text,
        link_preview=False,
        parse_mode="markdown",
        buttons=[Button.url("Click here To Refresh Token", url=shortenedUrl)],
    )


@bot.on(
    events.NewMessage(
        pattern=r"/start (?!token_)([0-9a-f]{8}-[0-9a-f]{4}-[0-5][0-9a-f]{3}-[089ab][0-9a-f]{3}-[0-9a-f]{12})",
        incoming=True,
        outgoing=False,
        func=lambda x: x.is_private,
    )
)
async def start_ntoken(m: Message):
    if m.sender_id not in ADMINS:
        if_token_avl = db.get(f"active_{m.sender_id}")
        if not if_token_avl:
            return await m.reply(
                "Your account is deactivated. send /gen to get activate it again."
            )
    text = m.pattern_match.group(1)
    fileid = db.get_key(str(text))
    if fileid:
        return await VideoSender.forward_file(
            file_id=fileid, message=m, client=bot, uid=text.strip()
        )
    else:
        return await m.reply("""your requested file is not available.""")


@bot.on(
    events.NewMessage(
        pattern=r"/start token_([0-9a-f]{8}-[0-9a-f]{4}-[0-5][0-9a-f]{3}-[089ab][0-9a-f]{3}-[0-9a-f]{12})",
        incoming=True,
        outgoing=False,
        func=lambda x: x.is_private,
    )
)
async def start_token(m: Message):
    uuid = m.pattern_match.group(1).strip()
    check_if = await is_user_on_chat(bot, FORCE_LINK, m.peer_id)
    if not check_if:
        return await m.reply(
            "You haven't joined @RoldexVerse or @RoldexVerseChats yet. Please join the channel and then send me the link again.\nThank you!",
            buttons=[
                [
                    Button.url("RoldexVerse", url="https://t.me/RoldexVerse"),
                    Button.url("RoldexVerseChats",
                               url="https://t.me/RoldexVerseChats"),
                ],
                [
                    Button.url(
                        "ReCheck ♻️",
                        url=f"https://{BOT_USERNAME}.t.me?start={uuid}",
                    ),
                ],
            ],
        )
    is_user_active = db.get(f"active_{m.sender_id}")
    if is_user_active:
        ttl = db.ttl(f"active_{m.sender_id}")
        t = hr.Time(str(ttl), default_unit=hr.Time.Unit.SECOND)
        return await m.reply(
            f"""You are already active.
Your session will expire in {t.to_humanreadable()}."""
        )
    if_token_avl = db.get(f"token_{uuid}")
    if not if_token_avl:
        return await generate_token(m)
    sender_id, shortenedUrl = if_token_avl.split("|")
    if m.sender_id != int(sender_id):
        return await m.reply(
            "Your token is invalid. Please try again.\n Hit /gen to get a new token."
        )
    set_user_active = db.set(f"active_{m.sender_id}", time.time(), ex=3600)
    db.delete(f"token_{uuid}")
    if set_user_active:
        return await m.reply("Your account is active. It will expire after 1 hour.")


@bot.on(
    events.NewMessage(
        pattern="/remove (.*)",
        incoming=True,
        outgoing=False,
        from_users=ADMINS,
    )
)
async def remove(m: UpdateNewMessage):
    user_id = m.pattern_match.group(1)
    if db.get(f"check_{user_id}"):
        db.delete(f"check_{user_id}")
        await m.reply(f"Removed {user_id} from the list.")
    else:
        await m.reply(f"{user_id} is not in the list.")


@bot.on(
    events.NewMessage(
        pattern="/removeall",
        incoming=True,
        outgoing=False,
        from_users=ADMINS,
    )
)
async def removeall(m: UpdateNewMessage):
    remove_all_videos()
    return await m.reply("Removed all videos from the list.")


bot.start(bot_token=BOT_TOKEN)
bot.run_until_disconnected()
