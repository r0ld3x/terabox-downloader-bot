import re
from pprint import pp
from urllib.parse import parse_qs, urlparse

import requests

from tools import get_formatted_size


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


def get_urls_from_string(string: str) -> list[str]:
    """
    Extracts URLs from a given string.

    Args:
        string (str): The input string from which to extract URLs.

    Returns:
        list[str]: A list of URLs extracted from the input string. If no URLs are found, an empty list is returned.
    """
    pattern = r"(https?://\S+)"
    urls = re.findall(pattern, string)
    urls = [url for url in urls if check_url_patterns(url)]
    if not urls:
        return []
    return urls[0]


def find_between(data: str, first: str, last: str) -> str | None:
    """
    Searches for the first occurrence of the `first` string in `data`,
    and returns the text between the two strings.

    Args:
        data (str): The input string.
        first (str): The first string to search for.
        last (str): The last string to search for.

    Returns:
        str | None: The text between the two strings, or None if the
            `first` string was not found in `data`.
    """
    try:
        start = data.index(first) + len(first)
        end = data.index(last, start)
        return data[start:end]
    except ValueError:
        return None


def extract_surl_from_url(url: str) -> str | None:
    """
    Extracts the surl parameter from a given URL.

    Args:
        url (str): The URL from which to extract the surl parameter.

    Returns:
        str: The surl parameter, or False if the parameter could not be found.
    """
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    surl = query_params.get("surl", [])

    if surl:
        return surl[0]
    else:
        return False


def get_data(url: str):
    netloc = urlparse(url).netloc
    url = url.replace(netloc, "1024terabox.com")
    response = requests.get(
        url,
        data="",
    )
    if not response.status_code == 200:
        return False
    default_thumbnail = find_between(response.text, 'og:image" content="', '"')

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Content-Type": "application/json",
        "Origin": "https://ytshorts.savetube.me",
        "Alt-Used": "ytshorts.savetube.me",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }

    response = requests.post(
        "https://ytshorts.savetube.me/api/v1/terabox-downloader",
        headers=headers,
        json={"url": url},
    )
    if response.status_code != 200:
        return False
    response = response.json()
    responses = response.get("response", [])
    if not responses:
        return False
    resolutions = responses[0].get("resolutions", [])
    if not resolutions:
        return False
    download = resolutions.get("Fast Download", "")
    video = resolutions.get("HD Video", "")

    response = requests.request(
        "HEAD",
        video,
        data="",
    )
    content_length = response.headers.get("Content-Length", 0)
    if not content_length:
        content_length = None
    idk = response.headers.get("content-disposition")
    if idk:
        fname = re.findall('filename="(.+)"', idk)
    else:
        fname = None
    response = requests.head(
        download,
    )

    direct_link = response.headers.get("location")
    data = {
        "file_name": (fname[0] if fname else None),
        "link": (video if video else None),
        "direct_link": (direct_link if direct_link else download if list else None),
        "thumb": (default_thumbnail if default_thumbnail else None),
        "size": (get_formatted_size(int(content_length)) if content_length else None),
        "sizebytes": (int(content_length) if content_length else None),
    }
    return data
