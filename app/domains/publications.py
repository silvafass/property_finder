from typing import List, Tuple
from kink import inject
from sqlmodel import Session, select, desc, func, or_, col
from datetime import UTC, datetime, timedelta
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
def urls_by_publisher(
    publisher: str,
    slice: tuple = None,
    look_back: timedelta = timedelta(hours=2),
    only_inspect: bool = False,
    session: Session = None,
) -> Tuple[int, List[str]]:
    with session:
        conditionals = [
            PropertyPublication.publisher == publisher,
            (
                or_(
                    PropertyPublication.updated_at
                    > datetime.now(UTC) - look_back,
                    col(PropertyPublication.broker).is_(None),
                )
                if look_back
                else True
            ),
            (
                col(PropertyPublication.to_inspect).is_(True)
                if only_inspect
                else True
            ),
            col(PropertyPublication.deleted).is_not(True),
        ]
        statement_count = select(func.count(PropertyPublication.url)).where(
            *conditionals
        )
        statement_url = (
            select(PropertyPublication.url)
            .where(*conditionals)
            .order_by(desc(PropertyPublication.created_at))
        )
        if slice:
            statement_url = statement_url.slice(*slice)
        return session.exec(statement_count).one(), list(
            session.exec(statement_url).all()
        )


@inject
def already_have_photo(
    url: str,
    session: Session,
) -> bool:
    with session:
        return session.exec(
            select(col(PropertyPublication.url).is_not(None)).where(
                PropertyPublication.url == url
            )
        ).first()
