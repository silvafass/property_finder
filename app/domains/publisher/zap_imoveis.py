from app.domains.publisher import Publisher
from typing import Self
from playwright.async_api import Page


class ZapImoveis(Publisher):

    name: str = "Zap Imoveis"
    website: str = "https://www.zapimoveis.com.br/"

    async def find(self, page: Page) -> Self:
        await page.wait_for_timeout(1000 * 5)
        print(await page.title())
