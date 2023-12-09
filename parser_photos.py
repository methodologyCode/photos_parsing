import asyncio
import http
import os
import pathlib
from http import HTTPStatus

import aiohttp
from bs4 import BeautifulSoup

from utils import logger, FailedRequestApi

AMOUNT_OF_ACTRESS = 3
AMOUNT_OF_PHOTOS = 2


async def get_html(url, user_agent):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=user_agent) as response:
                response_text = await response.text()
    except aiohttp.ClientError as e:
        logger.critical(f"Запрос провалился: {e}")
        raise FailedRequestApi(f"Запрос провалился: {e}")

    if response.status != HTTPStatus.OK:
        logger.error(f"Ответ сервера: {response.status}")
        raise FailedRequestApi(f"Ответ сервера: {response.status}")

    return BeautifulSoup(response_text, "lxml")


def get_list_links_actress(soup):
    article_list = soup.find("div", {"id": "content"}).find_all("article")
    links = []

    for item in article_list:
        try:
            url = item.find("footer",
                            {"class": "entry-meta"}).find_all("a")[-2]
            links.append(url.get("href"))
        except (AttributeError, IndexError):
            continue
    return links


def get_list_links_photos(soup):
    entry_content = soup.find("div", {"class": "entry-content"})
    a_list = entry_content.find_all("a")
    name = (
        soup.find("div", {"id": "content"})
        .find("h1", {"class": "entry-title"})
        .text
    )
    links = []

    for item in a_list:
        try:
            url = item.get("href")

            if url.split(".")[-1] == "jpg":
                links.append(url)

        except AttributeError:
            continue

    return "-".join(name.split(" ")[:2]), links[:AMOUNT_OF_PHOTOS]


async def download_images(link, user_agent):
    html = await get_html(link, user_agent)
    name, links = get_list_links_photos(html)
    result = await download_img(name, links, user_agent=user_agent)
    print(result)


async def download_img(name, imgs, user_agent=None):
    folder = os.path.abspath(os.getcwd())
    pathlib.Path(rf"{folder}/photos/{name}").mkdir(parents=True, exist_ok=True)
    count = 0
    async with aiohttp.ClientSession() as session:
        for img in imgs:
            count += 1
            async with session.get(img, headers=user_agent) as response:
                if response.status != http.HTTPStatus.OK:
                    logger.error(f"Ответ сервера: {response.status}")
                    raise FailedRequestApi(f"Ответ сервера: {response.status}")

                with open(
                    rf"{folder}/photos/{name}/{name}-{count}.jpg", "wb"
                ) as f:
                    while True:
                        chunk = await response.content.read(1024)
                        if not chunk:
                            break
                        f.write(chunk)
    return f"Фото {name} скачаны"


async def main():
    user_agent = {
        "User-Agent": "Mozilla/5.0 (Linux NT 10.0; x64)"
        "AppleWebKit/537.36 (KHTML, like Gecko)"
        "Chrome/102.0.0.0 Safari/537.36"
    }
    url = "https://thefappeningblog.com/tag/leaked-celebs/"
    html = await get_html(url, user_agent=user_agent)
    links = get_list_links_actress(html)

    coroutines = []
    for link in links[:AMOUNT_OF_ACTRESS]:
        if any(keyword in link for keyword in ["photo/", "photos/", "pics"]):
            coroutines.append(download_images(link, user_agent))

    await asyncio.gather(*coroutines)


if __name__ == "__main__":
    asyncio.run(main())
