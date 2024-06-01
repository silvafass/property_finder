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
        browser = await playwright.chromium.launch(
            channel=settings.browser_channel,
            headless=settings.browser_headless,
        )
        try:
            yield browser
        finally:
            await browser.close()


@asynccontextmanager
async def new_browser_context() -> BrowserContext:
    async with launch_browser() as browser:
        browser: Browser
        context = await browser.new_context()
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
