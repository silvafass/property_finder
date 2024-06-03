from abc import ABC, abstractmethod
from playwright.async_api import Page
from app.domains.browser import load_page
from pydantic import BaseModel
from typing import Self


class Searcher(ABC):

    @abstractmethod
    async def search(self, page: Page):
        pass


class Publisher(ABC):

    name: str
    website: str
    searcherTypes: type[Searcher] = set()

    async def process(self) -> Self:
        for searcherType in self.searcherTypes:
            async with load_page(self.website) as page:
                page: Page
                searcherType: type[Searcher]
                await searcherType().search(page)
                await self.inspec(page)
        return self

    @abstractmethod
    async def inspec(self, page: Page) -> Self:
        pass


class ModelMapper:

    async def get_dict(self, model_constructor: type[BaseModel]) -> dict:
        data: dict = {}
        for key in model_constructor.model_fields.keys():
            if hasattr(self, key):
                data[key] = await getattr(self, key)()
        return data
