#!.venv/bin/python

import asyncio
from typing import List
from app.domains.publisher import Publisher
from kink import inject


@inject()
async def main(publishers: List[Publisher]):
    for publisher in publishers:
        await publisher.process()


if __name__ == "__main__":
    asyncio.run(main())
