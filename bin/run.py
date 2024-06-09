#!.venv/bin/python

import asyncio
from typing import List
from app.domains.publisher import Publisher
from kink import inject
import logging
import typer
from rich.logging import RichHandler
from rich.console import Console

app = typer.Typer(no_args_is_help=True, rich_markup_mode="markdown")

console = Console()
console.set_alt_screen(False)
logging.basicConfig(
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
    format="%(message)s",
    handlers=[RichHandler(console=console)],
)


@inject()
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
def finder(like: str = None):
    """
    Run Finder for properties publishers.

    * Pass `--like patter_name` if you want to filter publishers
    """

    async def inner():
        for publisher in get_publishers(like):
            await publisher.process()

    asyncio.run(inner())


@app.command()
def playground(like: str = None):
    """
    Run playground for publishers.

    * Pass `--like patter_name` if you want to filter publishers
    """

    async def inner():
        for publisher in get_publishers(like):
            await publisher.playground()

    asyncio.run(inner())


@app.callback()
def callback():
    """
    Property Finder o/
    """


if __name__ == "__main__":
    app()
