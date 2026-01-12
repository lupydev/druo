"""
Merchant model.
"""

from datetime import datetime
from typing import ClassVar
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class MerchantBase(SQLModel):
    """Base merchant attributes."""

    name: str = Field(max_length=255)
    email: str = Field(max_length=255, unique=True)


class Merchant(MerchantBase, table=True):
    """Merchant database model."""

    __tablename__: ClassVar[str] = "merchants"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class MerchantCreate(MerchantBase):
    """Schema for creating a merchant."""

    pass


class MerchantRead(MerchantBase):
    """Schema for reading a merchant."""

    id: UUID
    created_at: datetime
    updated_at: datetime
