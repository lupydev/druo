"""
Merchant Retry Configuration model.
"""

from datetime import datetime
from typing import ClassVar
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class RetryConfigBase(SQLModel):
    """Base retry config attributes."""

    # Global settings
    retry_enabled: bool = Field(default=True)
    max_attempts: int = Field(default=3, ge=1, le=5)

    # Insufficient funds settings
    insufficient_funds_enabled: bool = Field(default=True)
    insufficient_funds_delay: int = Field(default=1440, ge=1)  # 24 hours in minutes

    # Card declined settings
    card_declined_enabled: bool = Field(default=True)
    card_declined_delay: int = Field(default=60, ge=1)  # 1 hour
    # Network timeout settings
    network_timeout_enabled: bool = Field(default=True)
    network_timeout_delay: int = Field(default=0, ge=0)  # immediate

    # Processor downtime settings
    processor_downtime_enabled: bool = Field(default=True)
    processor_downtime_delay: int = Field(default=30, ge=1)  # 30 minutes


class MerchantRetryConfig(RetryConfigBase, table=True):
    """Merchant retry configuration database model."""

    __tablename__: ClassVar[str] = "merchant_retry_configs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    merchant_id: UUID = Field(foreign_key="merchants.id", unique=True)

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class RetryConfigRead(RetryConfigBase):
    """Schema for reading retry config."""

    id: UUID
    merchant_id: UUID
    created_at: datetime
    updated_at: datetime


class RetryConfigUpdate(SQLModel):
    """Schema for updating retry config. All fields optional."""

    retry_enabled: bool | None = None
    max_attempts: int | None = Field(default=None, ge=1, le=5)

    insufficient_funds_enabled: bool | None = None
    insufficient_funds_delay: int | None = None
    card_declined_enabled: bool | None = None
    card_declined_delay: int | None = None

    network_timeout_enabled: bool | None = None
    network_timeout_delay: int | None = None
    processor_downtime_enabled: bool | None = None
    processor_downtime_delay: int | None = None
