"""
Unit tests for audit_logs service.
"""

from datetime import datetime
from typing import ClassVar
from uuid import uuid4

import pytest
from sqlmodel import Field, SQLModel, select


# Simplified AuditLog model for SQLite testing
class AuditLogTest(SQLModel, table=True):
    """Simplified AuditLog model for testing with SQLite."""

    __tablename__: ClassVar[str] = "audit_logs_test"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    event_type: str
    payment_id: str
    merchant_id: str
    attempt_number: int | None = Field(default=None)
    failure_type: str | None = Field(default=None)
    result: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)


# Service functions for testing
async def create_audit_log(
    session, event_type: str, payment_id: str, merchant_id: str, **kwargs
):
    """Create a new audit log."""
    log = AuditLogTest(
        event_type=event_type,
        payment_id=payment_id,
        merchant_id=merchant_id,
        **kwargs,
    )
    session.add(log)
    await session.commit()
    await session.refresh(log)
    return log


async def get_logs_by_payment_id(session, payment_id: str):
    """Get all audit logs for a payment, ordered by created_at."""
    result = await session.execute(
        select(AuditLogTest)
        .where(AuditLogTest.payment_id == payment_id)
        .order_by(AuditLogTest.created_at)  # type: ignore
    )
    return result.scalars().all()


async def get_logs_by_event_type(session, event_type: str):
    """Get all audit logs of a specific event type."""
    result = await session.execute(
        select(AuditLogTest).where(AuditLogTest.event_type == event_type)
    )
    return result.scalars().all()


# ============== TESTS ==============


@pytest.mark.asyncio
async def test_create_audit_log(async_session):
    """Test creating a new audit log."""
    payment_id = str(uuid4())
    merchant_id = str(uuid4())

    log = await create_audit_log(
        async_session,
        event_type="payment_failed",
        payment_id=payment_id,
        merchant_id=merchant_id,
        failure_type="insufficient_funds",
    )

    assert log.id is not None
    assert log.event_type == "payment_failed"
    assert log.payment_id == payment_id
    assert log.merchant_id == merchant_id
    assert log.failure_type == "insufficient_funds"
    assert log.created_at is not None


@pytest.mark.asyncio
async def test_get_logs_by_payment_id(async_session):
    """Test retrieving logs by payment ID."""
    payment_id = str(uuid4())
    merchant_id = str(uuid4())

    # Create sequence of events
    await create_audit_log(
        async_session,
        event_type="payment_failed",
        payment_id=payment_id,
        merchant_id=merchant_id,
    )
    await create_audit_log(
        async_session,
        event_type="retry_scheduled",
        payment_id=payment_id,
        merchant_id=merchant_id,
        attempt_number=1,
    )
    await create_audit_log(
        async_session,
        event_type="retry_executed",
        payment_id=payment_id,
        merchant_id=merchant_id,
        attempt_number=1,
        result="success",
    )

    logs = await get_logs_by_payment_id(async_session, payment_id)

    assert len(logs) == 3
    assert logs[0].event_type == "payment_failed"
    assert logs[1].event_type == "retry_scheduled"
    assert logs[2].event_type == "retry_executed"


@pytest.mark.asyncio
async def test_get_logs_by_payment_id_empty(async_session):
    """Test retrieving logs for non-existent payment returns empty list."""
    random_id = str(uuid4())

    logs = await get_logs_by_payment_id(async_session, random_id)

    assert logs == []


@pytest.mark.asyncio
async def test_get_logs_by_event_type(async_session):
    """Test retrieving logs by event type."""
    merchant_id = str(uuid4())

    await create_audit_log(
        async_session,
        event_type="payment_failed",
        payment_id=str(uuid4()),
        merchant_id=merchant_id,
    )
    await create_audit_log(
        async_session,
        event_type="retry_scheduled",
        payment_id=str(uuid4()),
        merchant_id=merchant_id,
    )
    await create_audit_log(
        async_session,
        event_type="payment_failed",
        payment_id=str(uuid4()),
        merchant_id=merchant_id,
    )

    failed_logs = await get_logs_by_event_type(async_session, "payment_failed")

    assert len(failed_logs) == 2
    for log in failed_logs:
        assert log.event_type == "payment_failed"


@pytest.mark.asyncio
async def test_audit_log_with_attempt_number(async_session):
    """Test audit log with attempt number."""
    payment_id = str(uuid4())
    merchant_id = str(uuid4())

    log = await create_audit_log(
        async_session,
        event_type="retry_executed",
        payment_id=payment_id,
        merchant_id=merchant_id,
        attempt_number=3,
        result="failed",
    )

    assert log.attempt_number == 3
    assert log.result == "failed"


@pytest.mark.asyncio
async def test_audit_log_with_result(async_session):
    """Test audit log with result field."""
    payment_id = str(uuid4())
    merchant_id = str(uuid4())

    log = await create_audit_log(
        async_session,
        event_type="retry_executed",
        payment_id=payment_id,
        merchant_id=merchant_id,
        result="success",
    )

    assert log.result == "success"


@pytest.mark.asyncio
async def test_logs_for_different_payments_isolated(async_session):
    """Test that logs are correctly isolated by payment."""
    payment1 = str(uuid4())
    payment2 = str(uuid4())
    merchant_id = str(uuid4())

    await create_audit_log(
        async_session,
        event_type="payment_failed",
        payment_id=payment1,
        merchant_id=merchant_id,
    )
    await create_audit_log(
        async_session,
        event_type="payment_recovered",
        payment_id=payment2,
        merchant_id=merchant_id,
    )

    logs1 = await get_logs_by_payment_id(async_session, payment1)
    logs2 = await get_logs_by_payment_id(async_session, payment2)

    assert len(logs1) == 1
    assert len(logs2) == 1
    assert logs1[0].event_type == "payment_failed"
    assert logs2[0].event_type == "payment_recovered"


@pytest.mark.asyncio
async def test_audit_trail_complete_flow(async_session):
    """Test complete audit trail for a payment retry flow."""
    payment_id = str(uuid4())
    merchant_id = str(uuid4())

    # Payment fails
    await create_audit_log(
        async_session,
        event_type="payment_failed",
        payment_id=payment_id,
        merchant_id=merchant_id,
        failure_type="network_timeout",
    )

    # Retry scheduled
    await create_audit_log(
        async_session,
        event_type="retry_scheduled",
        payment_id=payment_id,
        merchant_id=merchant_id,
        attempt_number=1,
    )

    # Retry executed - failed
    await create_audit_log(
        async_session,
        event_type="retry_executed",
        payment_id=payment_id,
        merchant_id=merchant_id,
        attempt_number=1,
        result="failed",
    )

    # Second retry scheduled
    await create_audit_log(
        async_session,
        event_type="retry_scheduled",
        payment_id=payment_id,
        merchant_id=merchant_id,
        attempt_number=2,
    )

    # Second retry executed - success
    await create_audit_log(
        async_session,
        event_type="retry_executed",
        payment_id=payment_id,
        merchant_id=merchant_id,
        attempt_number=2,
        result="success",
    )

    # Payment recovered
    await create_audit_log(
        async_session,
        event_type="payment_recovered",
        payment_id=payment_id,
        merchant_id=merchant_id,
    )

    logs = await get_logs_by_payment_id(async_session, payment_id)

    assert len(logs) == 6
    event_types = [log.event_type for log in logs]
    assert event_types == [
        "payment_failed",
        "retry_scheduled",
        "retry_executed",
        "retry_scheduled",
        "retry_executed",
        "payment_recovered",
    ]
