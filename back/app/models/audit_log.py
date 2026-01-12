"""
Retry Audit Log model - for compliance and tracking.
"""

from datetime import datetime
from typing import Any, ClassVar, Dict
from uuid import UUID, uuid4

from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlmodel import Column, Field, SQLModel

from app.models.payment import FailureType


class RetryAuditLog(SQLModel, table=True):
    """Retry audit log database model for compliance."""

    __tablename__: ClassVar[str] = "retry_audit_logs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    event_type: str = Field(max_length=50)
    # Values: 'payment_failed', 'classified', 'retry_scheduled', 'retry_executed',
    #         'retry_success', 'retry_failed', 'exhausted', 'rate_limited'

    payment_id: UUID | None = Field(default=None, foreign_key="payments.id")
    merchant_id: UUID | None = Field(default=None, foreign_key="merchants.id")

    attempt_number: int | None = Field(default=None)
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
    result: str | None = Field(default=None, max_length=20)

    # Non-sensitive payment details
    card_last4: str | None = Field(default=None, max_length=4)
    amount_cents: int | None = Field(default=None)
    currency: str | None = Field(default=None, max_length=3)

    # Additional context
    metadata_json: Dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))

    created_at: datetime = Field(default_factory=datetime.now)
