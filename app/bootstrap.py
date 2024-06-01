from kink import di, inject
from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, create_engine

from app.settings import Settings
from app.domains.publisher import Publisher, ZapImoveis


@inject
def db_setup(settings: Settings) -> Engine:
    engine = create_engine(settings.db_connection_uri, echo=settings.db_echo)
    SQLModel.metadata.create_all(engine)
    return engine


@inject
def db_session(engine: Engine):
    return Session(engine)


def bootstrap_di() -> None:

    di[Settings] = Settings()

    di[Engine] = lambda _: db_setup()
    di[Session] = lambda _: db_session()

    di[ZapImoveis] = lambda _: ZapImoveis()
    di.add_alias(Publisher, ZapImoveis)
