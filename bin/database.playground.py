import asyncio
from time import time

from kink import inject
from sqlalchemy import Engine
from sqlmodel import Session, select

from app.domains.models import PropertyPublication, PropertyType, ProposalType


@inject
async def main(engine: Engine):
    with Session(engine) as session, session.begin():
        publication = PropertyPublication(
            url=f"https://test-{time()}.com",
            broker="broker-01",
            publisher="publisher-01",
            proposal=ProposalType.SELL,
            type=PropertyType.APTO,
            price=220000.05,
        )
        session.add(publication)

    with Session(engine) as session:
        statement = select(PropertyPublication)
        for publication in session.exec(statement):
            print(publication)


if __name__ == "__main__":
    asyncio.run(main())
