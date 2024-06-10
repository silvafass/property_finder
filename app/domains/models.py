from datetime import UTC, datetime
from enum import StrEnum, auto
from typing import Optional

from sqlmodel import Field, SQLModel


class ProposalType(StrEnum):
    SELL = auto()
    RENT = auto()
    OTHERS = auto()


class PropertyType(StrEnum):
    HOUSE = auto()
    APTO = auto()
    CONDO_HOUSE = auto()
    TOWNHOUSES = auto()
    OTHERS = auto()


class PropertyPublication(SQLModel, table=True):
    url: str = Field(primary_key=True)
    search_url: Optional[str] = None
    publication_created_at: Optional[datetime] = None
    publication_updated_at: Optional[datetime] = None
    description: Optional[str] = None
    details: Optional[str] = None
    printscreen: Optional[bytes] = None
    address: Optional[str] = None
    broker: Optional[str] = None
    publisher: Optional[str] = None
    proposal: Optional[str] = None
    type: Optional[str] = None

    square_meter: Optional[int] = None
    bedrooms: Optional[int] = None
    suites: Optional[int] = None
    bathrooms: Optional[int] = None
    car_spaces: Optional[int] = None
    floor: Optional[int] = None
    balcony: Optional[int] = None

    buy_price: Optional[float] = None
    rent_price: Optional[float] = None
    iptu_tax: Optional[float] = None
    condominium_fee: Optional[float] = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    to_inspect: Optional[bool] = None
    deleted: Optional[bool] = None
