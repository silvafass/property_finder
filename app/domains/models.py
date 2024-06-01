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


class PropertyPublication(SQLModel, table=True):
    url: str = Field(primary_key=True)
    published_at: Optional[datetime] = None
    description: Optional[str] = None
    details: Optional[str] = None
    printscreen: Optional[bytes] = None
    address: Optional[str] = None
    broker: str
    publisher: str
    proposal: str
    type: str

    square_meter: Optional[int] = None
    bedrooms: Optional[int] = None
    suites: Optional[int] = None
    bathrooms: Optional[int] = None
    car_spaces: Optional[int] = None
    floor: Optional[int] = None
    balcony: Optional[int] = None

    price: float
    iptu_value: Optional[float] = None
    maintenance_fee_value: Optional[float] = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    deleted: Optional[bool] = None
