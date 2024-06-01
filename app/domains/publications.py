from typing import List

from kink import inject
from sqlmodel import Session, select

from app.domains.models import PropertyPublication


@inject
def add(publication: PropertyPublication, session: Session):
    with session, session.begin():
        session.add(publication)


@inject
def get_all(session: Session) -> List[PropertyPublication]:
    with session:
        statement = select(PropertyPublication)
        return list(session.exec(statement).all())
