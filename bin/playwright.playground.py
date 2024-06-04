#!.venv/bin/python

import asyncio

from playwright.async_api import Page

from app.domains.browser import load_page
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    async with load_page("http://playwright.dev") as page:
        page: Page
        await page.wait_for_timeout(1000 * 5)
        logger.info(await page.title())


asyncio.run(main())
