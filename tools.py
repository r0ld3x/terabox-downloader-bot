import asyncio
import os
import re
import time
import traceback
from urllib.parse import parse_qs, urlparse

from fuzzywuzzy import process
from pyrogram import Client, client
from pyrogram.enums import ParseMode
from pyrogram.types import Message

from cansend import CanSend
from config import CHAT_ID


def check_url_patterns(url):
    patterns = [
        r"ww\.mirrobox\.com",
        r"www\.nephobox\.com",
        r"freeterabox\.com",
        r"www\.freeterabox\.com",
        r"1024tera\.com",
        r"4funbox\.co",
        r"www\.4funbox\.com",
        r"mirrobox\.com",
        r"nephobox\.com",
        r"terabox\.app",
        r"terabox\.com",
        r"www\.terabox\.ap",
        r"www\.terabox\.com",
        r"www\.1024tera\.co",
        r"www\.momerybox\.com",
        r"teraboxapp\.com",
        r"momerybox\.com",
        r"tibibox\.com",
        r"www\.tibibox\.com",
        r"www\.teraboxapp\.com",
    ]

    for pattern in patterns:
        if re.search(pattern, url):
            return True

    return False


def get_urls_from_string(string):
    pattern = r"(https?://\S+)"
    urls = re.findall(pattern, string)
    urls = [url for url in urls if check_url_patterns(url)]
    if not urls:
        return
    return urls[0]


def extract_surl_from_url(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    surl = query_params.get("surl", None)

    if surl:
        return surl[0]
    else:
        return False


def get_formatted_size(size_bytes):
    if size_bytes >= 1024 * 1024:
        size = size_bytes / (1024 * 1024)
        unit = "MB"
    elif size_bytes >= 1024:
        size = size_bytes / 1024
        unit = "KB"
    else:
        size = size_bytes
        unit = "b"

    return f"{size:.2f} {unit}"


def convert_seconds(seconds):
    seconds = int(seconds)
    hours = seconds // 3600
    remaining_seconds = seconds % 3600
    minutes = remaining_seconds // 60
    remaining_seconds_final = remaining_seconds % 60

    if hours > 0:
        return f"{hours}h:{minutes}m:{remaining_seconds_final}s"
    elif minutes > 0:
        return f"{minutes}m:{remaining_seconds_final}s"
    else:
        return f"{remaining_seconds_final}s"


def get_total_size(files):
    return sum(os.path.getsize(file) for file in files)


def get_current_downloading(file_name: str = None):
    if os.path.exists(file_name):
        return file_name
    crdownload_files = [
        d
        for d in os.listdir()
        if d.endswith(".crdownload") or d.endswith(".mp4") or d.endswith(".mkv")
    ]
    if not crdownload_files:
        return

    matching_one = process.extract(file_name, crdownload_files, limit=1)
    name, ratio = matching_one[0]
    return False if not matching_one else name if ratio >= 80 else False


def progress_bar(
    current_downloaded, total_downloaded, download_speed, time_remaining, file_name
):
    bar_length = 40
    percent = current_downloaded / total_downloaded
    arrow = "+" * int(percent * bar_length) + ">"
    spaces = "-" * (bar_length - len(arrow))

    head_text = f"DOWNLOADING `{file_name}`"
    progress_bar = f"[{arrow + spaces}] {percent:.2%}"
    speed_line = f"Speed: **{get_formatted_size(download_speed)}/s**"
    time_line = f"Time Remaining: **{convert_seconds(time_remaining)}**"
    size_line = f"Size: **{get_formatted_size(current_downloaded)}** / **{get_formatted_size(total_downloaded)}**"
    return f"{head_text}\n{progress_bar}\n{speed_line}\n{time_line}\n{size_line}"


async def send_file(
    bot: Client, edit_message: Message, message: Message, file, file_name
):
    start_time = time.time()
    can_send = CanSend()

    async def progress_bar(
        current_downloaded,
        total_downloaded,
    ):
        if not can_send.can_send():
            return
        bar_length = 40
        percent = current_downloaded / total_downloaded
        arrow = "+" * int(percent * bar_length) + ">"
        spaces = "-" * (bar_length - len(arrow))

        elapsed_time = time.time() - start_time

        head_text = f"SENDING `{file_name}`"
        progress_bar = f"[{arrow + spaces}] {percent:.2%}"
        upload_speed = current_downloaded / elapsed_time if elapsed_time > 0 else 0
        speed_line = f"Speed: **{get_formatted_size(upload_speed)}/s**"

        time_remaining = (
            (total_downloaded - current_downloaded) / upload_speed
            if upload_speed > 0
            else 0
        )
        time_line = f"Time Remaining: `{convert_seconds(time_remaining)}`"

        size_line = f"Size: **{get_formatted_size(current_downloaded)}** / **{get_formatted_size(total_downloaded)}**"

        await edit_message.edit(
            f"{head_text}\n{progress_bar}\n{speed_line}\n{time_line}\n{size_line}",
            parse_mode=ParseMode.MARKDOWN,
        )

    sent = await bot.send_video(
        video=file,
        progress=progress_bar,
        supports_streaming=True,
        chat_id=CHAT_ID,
    )

    await bot.send_video(
        video=str(sent.video.file_id),
        supports_streaming=True,
        chat_id=message.chat.id,
        caption=f"""
Title: `{file_name}`
""",
        protect_content=True,
        has_spoiler=True,
        reply_to_message_id=message.id,
        file_name=file_name,
    )

    try:
        await bot.delete_messages(message.chat.id, edit_message.id)
        if sent or not sent:
            if os.path.exists(file):
                os.remove(file)
    except:
        pass


def get_file_name(file_name: str = None):
    if os.path.exists(file_name):
        return file_name
    crdownload_files = [d for d in os.listdir() if not d.endswith(".crdownload")]
    if not crdownload_files:
        return

    matching_one = process.extract(file_name, crdownload_files, limit=1)
    name, ratio = matching_one[0]
    return False if not matching_one else name if ratio >= 80 else False


async def download_and_send(
    bot: client,
    message: Message,
    edit_message: Message,
    file_name: str = None,
    total_size: int = None,
):
    timeout_seconds = 10
    start_time = time.time()
    if not file_name:
        return
    crdownload_file = get_current_downloading(file_name)
    last_update = time.time()
    while (
        not crdownload_file
        and time.time() - start_time > timeout_seconds
        and not os.path.exists(crdownload_file.replace(".crdownload", ""))
    ):
        crdownload_file = get_current_downloading(file_name)
    try:
        if (
            not isinstance(crdownload_file, bool)
            and os.path.exists(crdownload_file.replace(".crdownload", ""))
        ) or (os.path.exists(file_name)):
            crdownload_file = file_name
            raise Exception()
        if not crdownload_file:
            return await edit_message.edit("SOMETHING WENT WRONG")

        if os.path.exists(crdownload_file.replace(".crdownload", "")):
            crdownload_file = file_name
            raise Exception()
        previous_size = os.path.getsize(crdownload_file)
        previous_time = time.time()
        can_send_instance = CanSend()
        while (time.time() - last_update) < 15:
            if os.path.exists(crdownload_file.replace(".crdownload", "")):
                crdownload_file = file_name
                raise Exception()
            current_size = os.path.getsize(crdownload_file)
            progress = current_size / total_size * 100
            elapsed_time = time.time() - previous_time
            size_difference = current_size - previous_size
            download_speed = size_difference / elapsed_time if elapsed_time > 0 else 0

            remaining_time = (
                (total_size - current_size) / download_speed
                if download_speed > 0
                else 0
            )
            if can_send_instance.can_send():
                await edit_message.edit(
                    progress_bar(
                        current_size,
                        total_size,
                        download_speed,
                        remaining_time,
                        file_name,
                    )
                )

            if previous_size != current_size:
                last_update = time.time()

            previous_size = current_size
            previous_time = time.time()
    except Exception as e:
        await asyncio.sleep(2)
        local_file_name = get_file_name(file_name)

        if local_file_name:
            await send_file(
                bot=bot,
                edit_message=edit_message,
                message=message,
                file=local_file_name,
                file_name=local_file_name,
            )
        else:
            await edit_message.edit("SOMETHING WENT WRONG.")
            traceback.print_exc()
    finally:
        if local_file_name and os.path.exists(local_file_name):
            os.remove(local_file_name)
