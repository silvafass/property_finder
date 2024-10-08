#!.venv/bin/python

import asyncio
from time import time

from app.domains import publications
from app.domains.models import PropertyPublication, PropertyType, ProposalType
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    publications.add(
        PropertyPublication(
            url=f"https://test-{time()}.com",
            broker="broker-01",
            publisher="publisher-01",
            proposal=ProposalType.SELL,
            type=PropertyType.APTO,
            price=220000.05,
        )
    )

    for publication in publications.get_all():
        publication: PropertyPublication
        logger.info(
            publication.model_dump_json(
                indent=2, include=["url", "created_at"]
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
