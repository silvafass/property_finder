from abc import ABC, abstractmethod
from playwright.async_api import Page
from app.domains.browser import load_page
from typing import Self


class Publisher(ABC):

    name: str
    website: str

    async def process(self) -> Self:
        async with load_page(self.website) as page:
            page: Page
            return await self.find(page)

    @abstractmethod
    async def find(self, page: Page) -> Self:
        pass
