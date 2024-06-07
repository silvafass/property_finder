from abc import ABC, abstractmethod
from playwright.async_api import Page, TimeoutError, Locator
from app.domains.browser import load_page
from pydantic import BaseModel
from typing import Self, TypeVar, Generic, SupportsAbs, Callable
import logging
from time import time
from app.exceptions import HiddenElementError
import inspect
from functools import wraps

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


T = TypeVar("T", bound=SupportsAbs[Locator])


def visible_check(locator: Locator, function: Callable):
    @wraps(function)
    async def wrapper(*args, **kwargs):
        if await locator.count() <= 1 and await locator.is_hidden():
            raise HiddenElementError("Hidden Element")
        return await function(*args, **kwargs)

    return wrapper


class ModelMapper(Generic[T]):

    def _visible(self, locator: T) -> T:
        for key, _ in inspect.getmembers(locator):
            if (
                key not in ["is_hidden", "count"]
                and inspect.ismethod(getattr(locator, key))
                and inspect.iscoroutinefunction(getattr(locator, key))
            ):
                setattr(
                    locator, key, visible_check(locator, getattr(locator, key))
                )
        return locator

    async def get_dict(self, model_constructor: type[BaseModel]) -> dict:
        data: dict = {}
        for key in model_constructor.model_fields.keys():
            try:
                if hasattr(self, key):
                    data[key] = await getattr(self, key)()
            except (
                TimeoutError,
                HiddenElementError,
                ValueError,
                TypeError,
            ) as ex:
                logger.warning(
                    "Failed to get %s information: %s", key, str(ex)
                )
        return data
