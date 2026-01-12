"""
Retry Job model.
"""

from datetime import datetime
from enum import StrEnum
from typing import ClassVar, Optional
from uuid import UUID, uuid4

from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlmodel import Column, Field, SQLModel

from app.models.payment import FailureType


class RetryJobStatus(StrEnum):
    """Retry job status enum."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RetryJob(SQLModel, table=True):
    """Retry job database model."""

    __tablename__: ClassVar[str] = "retry_jobs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    payment_id: UUID = Field(foreign_key="payments.id")
    merchant_id: UUID = Field(foreign_key="merchants.id")

    attempt_number: int
    failure_type: FailureType
    failure_type: FailureType = Field(
        sa_column=Column(
            PG_ENUM(
                FailureType,
                name="failure_type",  # Debe coincidir con el nombre en la DB
                create_type=False,  # No crear, ya existe
                schema="public",  # Schema donde está el tipo
                values_callable=lambda enum: [e.value for e in enum],
            ),
            nullable=False,
        ),
    )

    # Scheduling
    scheduled_at: datetime
    executed_at: Optional[datetime] = Field(default=None)

    # Status
    status: RetryJobStatus = Field(
        default=RetryJobStatus.PENDING,
        sa_column=Column(
            PG_ENUM(
                RetryJobStatus,
                name="retry_status",  # Verifica el nombre en la BD
                create_type=False,
                schema="public",
                values_callable=lambda enum: [e.value for e in enum],
            ),
            nullable=False,
        ),
    )
    result_code: Optional[str] = Field(default=None, max_length=100)
    result_message: Optional[str] = Field(default=None)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
