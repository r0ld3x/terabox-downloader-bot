import os
import re
import traceback
import uuid
from contextlib import suppress
from io import BytesIO
from urllib.parse import parse_qs, urlparse

import requests
from PIL import Image
from telethon import TelegramClient

from config import BOT_USERNAME, PUBLIC_EARN_API
from redis_db import db


def check_url_patterns(url: str) -> bool:
    """
    Check if the given URL matches any of the known URL patterns for code hosting services.

    Parameters:
    url (str): The URL to be checked.

    Returns:
    bool: True if the URL matches a known pattern, False otherwise.
    """
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


def extract_code_from_url(url: str) -> str | None:
    """
    Extracts the code from a URL.

    Parameters:
        url (str): The URL to extract the code from.

    Returns:
        str: The extracted code, or None if the URL does not contain a code.
    """
    pattern1 = r"/s/(\w+)"
    pattern2 = r"surl=(\w+)"

    match = re.search(pattern1, url)
    if match:
        return match.group(1)

    match = re.search(pattern2, url)
    if match:
        return match.group(1)

    return None


def get_urls_from_string(string: str) -> str | None:
    """
    Extracts all URLs from a given string.

    Parameters:
        string (str): The input string.

    Returns:
        str: The first URL found in the input string, or None if no URLs were found.
    """
    pattern = r"(https?://\S+)"
    urls = re.findall(pattern, string)
    urls = [url for url in urls if check_url_patterns(url)]
    if not urls:
        return
    return urls[0]


def extract_surl_from_url(url: str) -> str:
    """
    Extracts the surl from a URL.

    Parameters:
        url (str): The URL to extract the surl from.

    Returns:
        str: The extracted surl, or None if the URL does not contain a surl.
    """
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    surl = query_params.get("surl", [])

    if surl:
        return surl[0]
    else:
        return False


def get_formatted_size(size_bytes: int) -> str:
    """
    Returns a human-readable file size from the given number of bytes.

    Parameters:
        size_bytes (int): The number of bytes to be converted to a file size.

    Returns:
        str: The file size in a human-readable format.
    """
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


def convert_seconds(seconds: int) -> str:
    """
    Convert seconds into a human-readable format.

    Parameters:
        seconds (int): The number of seconds to convert.

    Returns:
        str: The seconds converted to a human-readable format.
    """
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


async def is_user_on_chat(bot: TelegramClient, chat_id: int, user_id: int) -> bool:
    """
    Check if a user is present in a specific chat.

    Parameters:
        bot (TelegramClient): The Telegram client instance.
        chat_id (int): The ID of the chat.
        user_id (int): The ID of the user.

    Returns:
        bool: True if the user is present in the chat, False otherwise.
    """
    try:
        check = await bot.get_permissions(chat_id, user_id)
        return check
    except Exception:
        return False


async def download_file(
    url: str,
    filename: str,
    callback=None,
) -> str | bool:
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with suppress(
            requests.exceptions.ChunkedEncodingError,
        ):
            with open(filename, "wb") as file:
                for chunk in response.iter_content(chunk_size=1024):
                    file.write(chunk)
                    if callback:
                        downloaded_size = file.tell()
                        total_size = int(
                            response.headers.get("content-length", 0))
                        await callback(downloaded_size, total_size, "Downloading")
        # await asyncio.sleep(2)
        return filename
    except Exception as e:
        traceback.print_exc()
        print(f"Error downloading file: {e}")
        raise Exception(e)


def save_image_from_bytesio(image_bytesio, filename):
    try:
        image_bytesio.seek(0)
        image = Image.open(image_bytesio)
        image.save(filename)
        image.close()

        return filename

    except Exception as e:
        print(f"Error saving image: {e}")
        return False


def download_image_to_bytesio(url: str, filename: str) -> BytesIO | None:
    """
    Downloads an image from a URL and returns it as a BytesIO object.

    Args:
        url (str): The URL of the image to download.
        filename (str): The filename to save the image as.

    Returns:
        BytesIO: The image data as a BytesIO object, or None if the download failed.
    """
    try:
        response = requests.get(url)
        content = BytesIO()
        content.name = filename
        if response.status_code == 200:
            for chunk in response.iter_content(chunk_size=1024):
                content.write(chunk)
        else:
            return None
        content.seek(0)
        return content
    except Exception:
        return None


def remove_all_videos():
    current_directory = os.getcwd()

    video_extensions = [".mp4", ".mkv", ".webm"]

    try:
        for file_name in os.listdir(current_directory):
            if any(file_name.lower().endswith(ext) for ext in video_extensions):
                file_path = os.path.join(current_directory, file_name)

                os.remove(file_path)

    except Exception as e:
        print(f"Error: {e}")


def generate_shortenedUrl(
    sender_id: int,
):
    try:
        uid = str(uuid.uuid4())
        data = requests.get(
            "https://publicearn.com/api",
            params={
                "api": PUBLIC_EARN_API,
                "url": f"https://t.me/{BOT_USERNAME}?start=token_{uid}",
                "alias": uid.split("-", maxsplit=2)[0],
            },
        )
        data.raise_for_status()
        data_json = data.json()
        if data_json.get("status") == "success":
            url = data_json.get("shortenedUrl")
            db.set(f"token_{uid}", f"{sender_id}|{url}", ex=21600)
            return url
        else:
            return None
    except Exception as e:
        return None
