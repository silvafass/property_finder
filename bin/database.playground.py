import asyncio

from sqlmodel import Session, SQLModel, create_engine, select

from app.domains.models import PropertyPublication, PropertyType, ProposalType


async def main():
    engine = create_engine("sqlite:///data.db", echo=False)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session, session.begin():
        publication = PropertyPublication(
            url="https://test-04.com",
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
