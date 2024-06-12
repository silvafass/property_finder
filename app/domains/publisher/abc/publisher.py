from abc import ABC, abstractmethod
from playwright.async_api import Page, Locator, TimeoutError
from app.domains.browser import load_page
from pydantic import BaseModel
from typing import Self, TypeVar, Generic, SupportsAbs, Callable
import logging
from datetime import datetime, UTC
from app.exceptions import HiddenElementError
import inspect
from functools import wraps, partial

logger = logging.getLogger(__name__)


class Searcher(ABC):

    @abstractmethod
    async def search(self, page: Page):
        pass


class Publisher(ABC):

    name: str
    website: str
    searcherTypes: type[Searcher] = set()

    async def _search_process(self) -> Self:
        search_process_start_time = datetime.now(UTC)
        logger.info("Processing search on %s (%s)", self.name, self.website)
        for searcherType in self.searcherTypes:
            async with load_page(
                self.website,
                setup=partial(
                    self.setup_page, self.inspect_search_results_page.__name__
                ),
            ) as page:
                page: Page
                searcherType: type[Searcher]
                try:
                    browser_context = page.context
                    logger.info("Running %s...", searcherType.__name__)
                    await searcherType().search(page)
                    inspecting_start_time = datetime.now(UTC)
                    logger.info(
                        "Processing search result: %s", await page.title()
                    )
                    await self.inspect_search_results_page(page)
                    logger.info(
                        "Inspect search results completed (elapsed time %s)",
                        datetime.now(UTC) - inspecting_start_time,
                    )
                except Exception as ex:
                    if len(browser_context.pages) > 0:
                        logger.error(
                            "Something wrong on open page(s): %s",
                            [
                                page
                                for page in browser_context.pages
                                if not page.is_closed()
                            ],
                        )
                    raise ex
        logger.info(
            "Search process completed (elapsed time %s)",
            datetime.now(UTC) - search_process_start_time,
        )

    async def _publications_processs(self) -> Self:
        publications_process_start_time = datetime.now(UTC)
        urls_count = 0
        async for publication_url in self.query_publication_urls():
            if publication_url is None:
                continue
            try:
                async with load_page(
                    publication_url,
                    setup=partial(
                        self.setup_page, self.inspect_publication_page.__name__
                    ),
                ) as page:
                    page: Page
                    try:
                        urls_count = urls_count + 1
                        browser_context = page.context
                        logger.info(
                            "Processing publications page %s: %s",
                            urls_count,
                            publication_url,
                        )
                        await self.inspect_publication_page(
                            page, publication_url
                        )
                    except Exception as ex:
                        if len(browser_context.pages) > 0:
                            logger.error(
                                "Something wrong on open page(s): %s",
                                [
                                    page
                                    for page in browser_context.pages
                                    if not page.is_closed()
                                ],
                            )
                        raise ex
            except TimeoutError as ex:
                logger.warning(str(ex))
        logger.info(
            "Publications process completed (elapsed time %s)",
            datetime.now(UTC) - publications_process_start_time,
        )

    async def process(self) -> Self:
        processing_start_time = datetime.now(UTC)
        await self._search_process()
        await self._publications_processs()
        logger.info(
            "All processes completed (elapsed time %s)",
            datetime.now(UTC) - processing_start_time,
        )
        return self

    async def setup_page(self, load_type: str, page: Page, url: str):
        pass

    @abstractmethod
    async def inspect_search_results_page(self, page: Page) -> Self:
        pass

    async def query_publication_urls(self) -> str:
        yield None

    async def inspect_publication_page(
        self, page: Page, publication_url: str
    ) -> Self:
        pass

    async def playground(self) -> Self:
        logger.info("Let's play!")


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

    async def _before(self):
        pass

    async def get_dict(self, model_constructor: type[BaseModel]) -> dict:
        data: dict = {}

        try:
            await self._before()
        except (HiddenElementError, TypeError, TimeoutError, ValueError):
            pass

        for key in model_constructor.model_fields.keys():
            try:
                if hasattr(self, key):
                    data[key] = await getattr(self, key)()
            except (
                HiddenElementError,
                TypeError,
            ):
                pass
            except (
                TimeoutError,
                ValueError,
            ) as ex:
                logger.warning(
                    "Failed to get %s information: %s", key, str(ex)
                )
        return data
