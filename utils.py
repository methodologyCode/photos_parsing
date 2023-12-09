import logging
from logging import Formatter
from random import choice

import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler("debug.log", mode="a", encoding="UTF-8")
logger.addHandler(handler)
formatter = Formatter("{asctime}, {levelname}, {message}", style="{")
handler.setFormatter(formatter)


class FailedRequestApi(Exception):
    """Исключение для неудачного запроса."""
    pass


async def get_settings_request():
    user_agent = {
        "User-Agent": "Mozilla/5.0 (Linux NT 10.0; x64)"
        "AppleWebKit/537.36 (KHTML, like Gecko)"
        "Chrome/102.0.0.0 Safari/537.36"
    }
    url = "https://free-proxy-list.net/"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=user_agent) as response:
            response = await session.get("https://free-proxy-list.net/")
            soup = BeautifulSoup(await response.text(), "lxml")

    trs = soup.find("tbody").find_all("tr")

    proxies = []

    for tr in trs:
        tds = tr.find_all("td")
        ip = tds[0].text.strip()
        port = tds[1].text.strip()
        schema = "https" if "yes" in tds[6].text.strip() else "http"
        proxy = {"schema": schema, "address": ip + ":" + port}
        proxies.append(proxy)

    return choice(proxies), user_agent
