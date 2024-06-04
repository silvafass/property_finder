from abc import ABC, abstractmethod
from playwright.async_api import Page
from app.domains.browser import load_page
from pydantic import BaseModel
from typing import Self
import logging
from time import time

logger = logging.getLogger(__name__)


class Searcher(ABC):

    @abstractmethod
    async def search(self, page: Page):
        pass


class Publisher(ABC):

    name: str
    website: str
    searcherTypes: type[Searcher] = set()

    async def process(self) -> Self:
        processing_start_time = time()
        logger.info("Processing search on %s (%s)", self.name, self.website)
        for searcherType in self.searcherTypes:
            async with load_page(self.website) as page:
                page: Page
                searcherType: type[Searcher]
                logger.info("Running %s...", searcherType.__name__)
                await searcherType().search(page)
                inspecting_start_time = time()
                logger.info("Inspecting search result: %s", await page.title())
                await self.inspec(page)
                logger.info(
                    "Inspection completed (%s seconds)",
                    time() - inspecting_start_time,
                )
        logger.info(
            "Processing completed (%s seconds)", time() - processing_start_time
        )
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
