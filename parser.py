import asyncio
import http
import os
import pathlib
from http import HTTPStatus

import aiohttp
from bs4 import BeautifulSoup

from utils import logger, FailedRequestApi


async def get_html(url):
    user_agent = {'User-Agent': 'Mozilla/5.0 (Linux NT 10.0; x64)'
                                'AppleWebKit/537.36 (KHTML, like Gecko)'
                                'Chrome/102.0.0.0 Safari/537.36'}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=user_agent) as response:
                response_text = await response.text()
    except aiohttp.ClientError as e:
        logger.critical(f'Запрос провалился: {e}')
        raise FailedRequestApi(f'Запрос провалился: {e}')

    if response.status != HTTPStatus.OK:
        logger.error(f'Ответ сервера: {response.status}')
        raise FailedRequestApi(f'Ответ сервера: {response.status}')

    return BeautifulSoup(response_text, 'lxml')


async def get_list_links_actress(soup):
    article_list = soup.find('div', {'id': 'content'}).find_all('article')
    links = []

    for item in article_list:
        try:
            url = item.find('footer',
                            {'class': 'entry-meta'}).find_all('a')[-2]
            links.append(url.get('href'))
        except AttributeError:
            continue
    return links


async def get_list_links_photos(soup):
    a_list = soup.find('div', {'class': 'entry-content'}).find_all('a')
    name = soup.find('div', {'id': 'content'}).find('h1', {
        'class': 'entry-title'}).text
    links = []

    for item in a_list:
        try:
            url = item.get('href')

            if url.split('.')[-1] == 'jpg':
                links.append(url)

        except AttributeError:
            continue

    return '-'.join(name.split(' ')[:2]), links[0:3]


async def download_images(link):
    html = await get_html(link)
    name, links = await get_list_links_photos(html)
    await download_img(name, links)


async def download_img(name, imgs):
    folder = os.path.abspath(os.curdir)
    pathlib.Path(fr"{folder}\photos\{name}").mkdir(parents=True,
                                                   exist_ok=True)
    count = 0
    async with aiohttp.ClientSession() as session:
        for img in imgs:
            count += 1
            async with session.get(img) as response:

                if response.status != http.HTTPStatus.OK:
                    logger.error(f'Ответ сервера: {response.status}')
                    raise FailedRequestApi(f'Ответ сервера: {response.status}')

                with open(
                        fr"{folder}\photos\{name}\{name}-{count}.jpg",
                        'wb') as f:
                    while True:
                        chunk = await response.content.read(1024)
                        if not chunk:
                            break
                        f.write(chunk)


async def main():
    url = 'https://thefappeningblog.com/tag/leaked-celebs/'
    html = await get_html(url)
    links = await get_list_links_actress(html)

    coroutines = []
    for link in links[0:3]:
        if link.split('-')[-1] or [-2] in ['photo/', 'photos/', 'pics']:
            coroutines.append(download_images(link))

    await asyncio.gather(*coroutines)


if __name__ == '__main__':
    asyncio.run(main())
