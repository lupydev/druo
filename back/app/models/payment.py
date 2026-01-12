"""
Payment model.
"""

from datetime import datetime
from enum import StrEnum
from typing import ClassVar
from uuid import UUID, uuid4

from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlmodel import Column, Field, SQLModel


class PaymentStatus(StrEnum):
    """Payment status enum."""

    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    RETRYING = "retrying"
    RECOVERED = "recovered"
    EXHAUSTED = "exhausted"


class FailureType(StrEnum):
    """Payment failure type enum."""

    INSUFFICIENT_FUNDS = "insufficient_funds"
    CARD_DECLINED = "card_declined"
    NETWORK_TIMEOUT = "network_timeout"
    PROCESSOR_DOWNTIME = "processor_downtime"
    FRAUD = "fraud"
    EXPIRED = "expired"
    UNKNOWN = "unknown"


class PaymentBase(SQLModel):
    """Base payment attributes."""

    merchant_id: UUID = Field(foreign_key="merchants.id")
    amount_cents: int
    currency: str = Field(default="USD", max_length=3)
    description: str | None = Field(default=None, max_length=500)

    # Card info (tokenized)
    card_last4: str | None = Field(default=None, max_length=4)
    card_brand: str | None = Field(default=None, max_length=20)
    card_fingerprint: str | None = Field(default=None, max_length=100)

    # Processor info
    processor: str = Field(default="stripe", max_length=50)
    processor_payment_id: str | None = Field(default=None, max_length=255)


class Payment(PaymentBase, table=True):
    """Payment database model."""

    __tablename__: ClassVar[str] = "payments"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Status tracking
    status: PaymentStatus = Field(
        default=PaymentStatus.PENDING,
        sa_column=Column(
            PG_ENUM(
                PaymentStatus,
                name="payment_status",  # Debe coincidir con el nombre en la DB
                create_type=False,  # No crear, ya existe
                schema="public",  # Schema donde está el tipo
                values_callable=lambda enum: [e.value for e in enum],
            ),
            nullable=False,
        ),
    )
    failure_type: FailureType | None = Field(
        default=None,
        sa_column=Column(
            PG_ENUM(
                FailureType,
                name="failure_type",  # Debe coincidir con el nombre en la DB
                create_type=False,  # No crear, ya existe
                schema="public",  # Schema donde está el tipo
                values_callable=lambda enum: [e.value for e in enum],
            ),
            nullable=True,
        ),
    )

    failure_code: str | None = Field(default=None, max_length=100)
    failure_message: str | None = Field(default=None)

    # Retry tracking
    retry_count: int = Field(default=0)
    last_retry_at: datetime | None = Field(default=None)
    recovered_via_retry: bool = Field(default=False)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class PaymentRead(PaymentBase):
    """Schema for reading a payment."""

    id: UUID
    status: PaymentStatus
    failure_type: FailureType | None
    failure_code: str | None
    failure_message: str | None
    retry_count: int
    last_retry_at: datetime | None
    recovered_via_retry: bool
    created_at: datetime
    updated_at: datetime
