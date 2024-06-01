from kink import di, inject
from sqlalchemy import Engine
from sqlmodel import SQLModel, create_engine

from app.settings import Settings


@inject
def db_setup(settings: Settings) -> Engine:
    engine = create_engine(settings.db_connection_uri, echo=settings.db_echo)
    SQLModel.metadata.create_all(engine)
    return engine


def bootstrap_di() -> None:
    di[Settings] = Settings()
    di[Engine] = lambda di: db_setup()
