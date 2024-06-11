#!.venv/bin/python

import asyncio
from typing import List
from app.domains.publisher import Publisher
from kink import inject
import logging
import typer
from rich.logging import RichHandler
import rich
from app.settings import Settings

app = typer.Typer(
    no_args_is_help=True,
    rich_markup_mode="markdown",
    pretty_exceptions_enable=False,
)

rich.get_console().set_alt_screen(False)
rich.get_console().clear()
logging.basicConfig(
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
    format="%(message)s",
    handlers=[
        RichHandler(
            tracebacks_show_locals=True,
            rich_tracebacks=True,
            tracebacks_word_wrap=True,
        )
    ],
)


@inject
def get_publishers(
    like: str = None, publishers: List[Publisher] = []
) -> List[Publisher]:
    if like:
        filtered = [
            publisher
            for publisher in publishers
            if (like or "").lower() in publisher.name.lower()
            or like in publisher.website.lower()
        ]
        len(filtered) > 1 and typer.confirm(
            f"Are you sure you want to finder for {[
                publisher.name for publisher in filtered
            ]}?",
            abort=True,
        )
        return filtered
    return publishers


@app.command()
def all_process(like: str = None):
    """
    Perform all detailed search processing on the publishers website.

    * Pass `--like patter_name` if you want to filter publishers
    """

    async def inner():
        for publisher in get_publishers(like):
            await publisher.process()

    asyncio.run(inner())


@app.command()
def search_process(like: str = None):
    """
    Perform search processing on the publishers website.

    * Pass `--like patter_name` if you want to filter publishers
    """

    async def inner():
        for publisher in get_publishers(like):
            await publisher._search_process()

    asyncio.run(inner())


@app.command()
def detailed_info_process(like: str = None):
    """
    Perform publication info processing on the publishers website.

    * Pass `--like patter_name` if you want to filter publishers
    """

    async def inner():
        for publisher in get_publishers(like):
            await publisher._publications_processs()

    asyncio.run(inner())


@app.command()
def playground(like: str = None):
    """
    Peform playground in publishers.

    * Pass `--like patter_name` if you want to filter publishers
    """

    async def inner():
        for publisher in get_publishers(like):
            await publisher.playground()

    asyncio.run(inner())


@app.callback()
def callback(log: bool = True, only_inspect: bool = True):
    """
    Property Finder o/
    """
    if not log:
        logging.disable(logging.CRITICAL)

    @inject
    def inner(settings: Settings):
        if not only_inspect:
            settings.default_publisher_settings.only_inspect = only_inspect

    inner()


if __name__ == "__main__":
    app()
