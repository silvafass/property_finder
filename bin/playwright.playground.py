#!.venv/bin/python

import asyncio

from playwright.async_api import Page

from app.domains.browser import load_page


async def main():
    async with load_page("http://playwright.dev") as page:
        page: Page
        await page.wait_for_timeout(1000 * 5)
        print(await page.title())


asyncio.run(main())
