from contextlib import asynccontextmanager

from kink import inject
from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    async_playwright,
)

from app.settings import Settings


@inject
@asynccontextmanager
async def launch_browser(settings: Settings) -> Browser:
    async with async_playwright() as playwright:
        browser = await playwright.firefox.launch(
            channel=settings.browser_channel,
            headless=settings.browser_headless,
            args=settings.browser_args,
        )
        try:
            yield browser
        finally:
            await browser.close()


@inject
@asynccontextmanager
async def new_browser_context(settings: Settings) -> BrowserContext:
    async with launch_browser() as browser:
        browser: Browser
        context = await browser.new_context(
            no_viewport=settings.browser_no_viewport
        )
        try:
            yield context
        finally:
            await context.close()


@inject
@asynccontextmanager
async def load_page(
    url: str, settings: Settings, wait_for_timeout: int = 1000
) -> Page:
    async with new_browser_context() as context:
        context: BrowserContext
        page = await context.new_page()
        try:
            await page.goto(url)
            await page.wait_for_timeout(wait_for_timeout)
            yield page
        finally:
            await page.close()


class PageHelper:

    @staticmethod
    async def scroll_to_end(page: Page, pixels_to_scroll: int = 10):
        page_offsetHeight = None
        while page_offsetHeight != await page.evaluate(
            "document.body.offsetHeight"
        ):
            previous_page_offsetHeight = page_offsetHeight or 0
            page_offsetHeight = await page.evaluate(
                "document.body.offsetHeight"
            )
            remaning_wheel = (
                page_offsetHeight - previous_page_offsetHeight
            ) / pixels_to_scroll
            remaning_wheel = int(remaning_wheel)
            for _ in range(remaning_wheel):
                await page.mouse.wheel(0, pixels_to_scroll)
                await page.wait_for_timeout(int(pixels_to_scroll / 2))
