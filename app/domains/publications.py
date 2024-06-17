from typing import List, Tuple, Optional, Literal
from kink import inject
from sqlmodel import Session, select, desc, asc, func, or_, col, and_
from datetime import UTC, datetime, timedelta
from app.domains.models import PropertyPublication
from pydantic import BaseModel


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
                if look_back and only_inspect
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


class SearchOrderBy(BaseModel):
    field: Optional[str]
    direction: Optional[Literal["ASC", "DESC"]]


class DateTimeSearch(BaseModel):
    back: Optional[datetime | timedelta] = None
    forward: Optional[datetime | timedelta] = None


class IntRangeSearch(BaseModel):
    back: Optional[int] = None
    forward: Optional[int] = None


class FloatRangeSearch(BaseModel):
    back: Optional[float] = None
    forward: Optional[float] = None


class ConditionsSearch(BaseModel):
    url: Optional[str] = None
    search_url: Optional[str] = None
    publication_created_at: Optional[DateTimeSearch] = None
    publication_updated_at: Optional[DateTimeSearch] = None
    description: Optional[str] = None
    details: Optional[str] = None
    address: Optional[str] = None
    broker: Optional[str] = None
    publisher: Optional[str] = None
    proposal: Optional[str] = None
    type: Optional[str] = None

    square_meter: Optional[IntRangeSearch] = None
    bedrooms: Optional[IntRangeSearch] = None
    suites: Optional[IntRangeSearch] = None
    bathrooms: Optional[IntRangeSearch] = None
    car_spaces: Optional[IntRangeSearch] = None
    floor: Optional[IntRangeSearch] = None
    balcony: Optional[IntRangeSearch] = None

    buy_price: Optional[FloatRangeSearch] = None
    rent_price: Optional[FloatRangeSearch] = None
    iptu_tax: Optional[FloatRangeSearch] = None
    condominium_fee: Optional[FloatRangeSearch] = None

    created_at: Optional[DateTimeSearch] = None
    updated_at: Optional[DateTimeSearch] = None
    to_inspect: Optional[bool] = None
    deleted: Optional[bool] = None


@inject
def search(
    like: str = None,
    conditions: ConditionsSearch = None,
    ordering: list[SearchOrderBy] = None,
    slice: tuple = None,
    session: Session = None,
) -> Tuple[int, List[PropertyPublication]]:
    with session:
        conditionals = []
        if like:
            like = f"%{like}%"
            conditionals.append(
                or_(
                    col(PropertyPublication.address).like(like),
                    col(PropertyPublication.broker).like(like),
                    col(PropertyPublication.description).like(like),
                    col(PropertyPublication.details).like(like),
                    col(PropertyPublication.proposal).like(like),
                    col(PropertyPublication.publisher).like(like),
                    col(PropertyPublication.type).like(like),
                )
            )
        if conditions:
            for field in conditions.model_dump(exclude_unset=True).keys():
                condition = getattr(conditions, field)
                match condition:
                    case condition if type(condition) in [DateTimeSearch]:
                        condition: DateTimeSearch
                        conditionals.append(
                            and_(
                                (
                                    col(getattr(PropertyPublication, field))
                                    >= datetime.now(UTC) - condition.back
                                    if condition.back
                                    else True
                                ),
                                (
                                    col(getattr(PropertyPublication, field))
                                    <= datetime.now(UTC) - condition.forward
                                    if condition.forward
                                    else True
                                ),
                            )
                        )
                    case condition if type(condition) in [
                        IntRangeSearch,
                        FloatRangeSearch,
                    ]:
                        conditionals.append(
                            and_(
                                (
                                    col(getattr(PropertyPublication, field))
                                    >= condition.back
                                    if condition.back
                                    else True
                                ),
                                (
                                    col(getattr(PropertyPublication, field))
                                    <= condition.forward
                                    if condition.forward
                                    else True
                                ),
                            )
                        )
                    case condition if type(condition) in [str]:
                        conditionals.append(
                            col(getattr(PropertyPublication, field)).like(
                                f"%{condition}%"
                            )
                        )
                    case False:
                        conditionals.append(
                            or_(
                                col(getattr(PropertyPublication, field)).is_(
                                    condition
                                ),
                                col(getattr(PropertyPublication, field)).is_(
                                    None
                                ),
                            )
                        )
                    case _:
                        conditionals.append(
                            col(getattr(PropertyPublication, field)).is_(
                                condition
                            )
                        )
        statement_count = select(func.count(PropertyPublication.url)).where(
            *conditionals
        )
        statement_url = (
            select(PropertyPublication)
            .where(*conditionals)
            .order_by(desc(PropertyPublication.created_at))
        )

        _ordering = []
        if ordering:
            for order_item in ordering:
                if order_item.direction == "DESC":
                    _ordering.append(
                        desc(getattr(PropertyPublication, order_item.field))
                    )
                else:
                    _ordering.append(
                        asc(getattr(PropertyPublication, order_item.field))
                    )
        if _ordering:
            statement_url = statement_url.order_by(None).order_by(*_ordering)

        if slice:
            statement_url = statement_url.slice(*slice)
        return session.exec(statement_count).one(), list(
            session.exec(statement_url).all()
        )


@inject
def py_url(
    url: str,
    session: Session,
) -> PropertyPublication:
    with session:
        return session.exec(
            select(PropertyPublication).where(PropertyPublication.url == url)
        ).first()
