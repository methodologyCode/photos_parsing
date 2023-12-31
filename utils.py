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
