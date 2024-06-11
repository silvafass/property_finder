from contextlib import asynccontextmanager

from kink import inject
from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    async_playwright,
    Locator,
)
from secrets import choice
from app.settings import Settings


@inject
@asynccontextmanager
async def launch_browser(settings: Settings) -> Browser:
    async with async_playwright() as playwright:
        match settings.browser_channel:
            case "chromium" | "chrome":
                browser_type = playwright.chromium
            case "firefox":
                browser_type = playwright.firefox
            case _:
                browser_type = playwright.chromium
        browser = await browser_type.launch(
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
    def _random_timeout(timeout: float):
        return choice(range(int(timeout / 2), int(timeout * 2)))

    @staticmethod
    async def scroll_to_end(
        page: Page,
        pixels_to_scroll: int = 10,
        locator: Locator = None,
        end: Locator = None,
    ) -> Locator:
        page_offsetHeight = None
        locator_index = 0
        while page_offsetHeight != await page.evaluate(
            "document.body.offsetHeight"
        ):
            previous_offsetHeight = page_offsetHeight or 0
            page_offsetHeight = await page.evaluate(
                "document.body.offsetHeight"
            )
            remaning_offsetHeight = page_offsetHeight - previous_offsetHeight
            remaning_wheel = remaning_offsetHeight / pixels_to_scroll
            for _ in range(int(remaning_wheel)):
                await page.mouse.wheel(0, pixels_to_scroll)
                await page.wait_for_timeout(
                    PageHelper._random_timeout(pixels_to_scroll)
                )
                if locator_index < await locator.count():
                    yield locator.nth(locator_index)
                    locator_index = locator_index + 1
                if end and await end.is_visible():
                    break
            for index in range(locator_index, await locator.count()):
                yield locator.nth(index)
                locator_index = locator_index + 1
            await page.wait_for_timeout(
                PageHelper._random_timeout(pixels_to_scroll)
            )
            if end and await end.is_visible():
                break
