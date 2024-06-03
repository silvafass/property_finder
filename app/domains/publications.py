from typing import List
from kink import inject
from sqlmodel import Session, select
from datetime import UTC, datetime
from app.domains.models import PropertyPublication


@inject
def save(data: dict, session: Session):
    with session, session.begin():
        model = session.get(PropertyPublication, data.get("url"))
        if model:
            for key in PropertyPublication.model_fields.keys():
                if data.get(key) is not None and data.get(key) != getattr(
                    model, key
                ):
                    setattr(model, key, data.get(key))
            model.updated_at = datetime.now(UTC)
            session.add(model)
        else:
            session.add(PropertyPublication(**data))


@inject
def get_all(session: Session) -> List[PropertyPublication]:
    with session:
        statement = select(PropertyPublication)
        return list(session.exec(statement).all())
