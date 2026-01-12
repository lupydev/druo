"""
Unit tests for payments service.
"""

from typing import ClassVar
from uuid import uuid4

import pytest
from sqlmodel import Field, SQLModel, select


# Simplified Payment model for SQLite testing (no PG_ENUM)
class PaymentTest(SQLModel, table=True):
    """Simplified Payment model for testing with SQLite."""

    __tablename__: ClassVar[str] = "payments_test"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    merchant_id: str
    amount_cents: int
    currency: str = Field(default="USD")
    status: str = Field(default="pending")
    failure_type: str | None = Field(default=None)
    processor: str = Field(default="stripe")
    retry_count: int = Field(default=0)


# Service functions for testing
async def create_payment(session, merchant_id: str, amount_cents: int, **kwargs):
    """Create a new payment."""
    payment = PaymentTest(merchant_id=merchant_id, amount_cents=amount_cents, **kwargs)
    session.add(payment)
    await session.commit()
    await session.refresh(payment)
    return payment


async def get_payment_by_id(session, payment_id: str):
    """Get payment by ID."""
    result = await session.execute(
        select(PaymentTest).where(PaymentTest.id == payment_id)
    )
    return result.scalar_one_or_none()


async def filter_payments(
    session,
    merchant_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
):
    """Filter payments by merchant and/or status."""
    query = select(PaymentTest)

    if merchant_id:
        query = query.where(PaymentTest.merchant_id == merchant_id)
    if status:
        query = query.where(PaymentTest.status == status)

    query = query.limit(limit)

    result = await session.execute(query)
    return result.scalars().all()


async def update_payment_status(session, payment_id: str, status: str):
    """Update payment status."""
    payment = await get_payment_by_id(session, payment_id)
    if payment:
        payment.status = status
        session.add(payment)
        await session.commit()
        await session.refresh(payment)
    return payment


async def increment_retry_count(session, payment_id: str):
    """Increment retry count for a payment."""
    payment = await get_payment_by_id(session, payment_id)
    if payment:
        payment.retry_count += 1
        session.add(payment)
        await session.commit()
        await session.refresh(payment)
    return payment


# ============== TESTS ==============


@pytest.mark.asyncio
async def test_create_payment(async_session):
    """Test creating a new payment."""
    merchant_id = str(uuid4())

    payment = await create_payment(
        async_session,
        merchant_id=merchant_id,
        amount_cents=5000,
        currency="USD",
        processor="stripe",
    )

    assert payment.id is not None
    assert payment.merchant_id == merchant_id
    assert payment.amount_cents == 5000
    assert payment.currency == "USD"
    assert payment.status == "pending"
    assert payment.retry_count == 0


@pytest.mark.asyncio
async def test_get_payment_by_id(async_session):
    """Test retrieving a payment by ID."""
    merchant_id = str(uuid4())

    created = await create_payment(
        async_session, merchant_id=merchant_id, amount_cents=10000
    )

    found = await get_payment_by_id(async_session, created.id)

    assert found is not None
    assert found.id == created.id
    assert found.amount_cents == 10000


@pytest.mark.asyncio
async def test_get_payment_by_id_not_found(async_session):
    """Test retrieving non-existent payment returns None."""
    random_id = str(uuid4())

    found = await get_payment_by_id(async_session, random_id)

    assert found is None


@pytest.mark.asyncio
async def test_filter_payments_by_merchant(async_session):
    """Test filtering payments by merchant_id."""
    merchant1 = str(uuid4())
    merchant2 = str(uuid4())

    await create_payment(async_session, merchant_id=merchant1, amount_cents=1000)
    await create_payment(async_session, merchant_id=merchant1, amount_cents=2000)
    await create_payment(async_session, merchant_id=merchant2, amount_cents=3000)

    payments = await filter_payments(async_session, merchant_id=merchant1)

    assert len(payments) == 2
    for p in payments:
        assert p.merchant_id == merchant1


@pytest.mark.asyncio
async def test_filter_payments_by_status(async_session):
    """Test filtering payments by status."""
    merchant_id = str(uuid4())

    await create_payment(
        async_session, merchant_id=merchant_id, amount_cents=1000, status="pending"
    )
    await create_payment(
        async_session, merchant_id=merchant_id, amount_cents=2000, status="failed"
    )
    await create_payment(
        async_session, merchant_id=merchant_id, amount_cents=3000, status="failed"
    )

    failed_payments = await filter_payments(async_session, status="failed")

    assert len(failed_payments) == 2
    for p in failed_payments:
        assert p.status == "failed"


@pytest.mark.asyncio
async def test_update_payment_status(async_session):
    """Test updating payment status."""
    merchant_id = str(uuid4())

    payment = await create_payment(
        async_session, merchant_id=merchant_id, amount_cents=5000, status="pending"
    )
    assert payment.status == "pending"

    updated = await update_payment_status(async_session, payment.id, "failed")

    assert updated is not None
    assert updated.status == "failed"


@pytest.mark.asyncio
async def test_increment_retry_count(async_session):
    """Test incrementing retry count."""
    merchant_id = str(uuid4())

    payment = await create_payment(
        async_session, merchant_id=merchant_id, amount_cents=5000
    )
    assert payment.retry_count == 0

    await increment_retry_count(async_session, payment.id)
    updated = await get_payment_by_id(async_session, payment.id)

    assert updated.retry_count == 1

    await increment_retry_count(async_session, payment.id)
    updated = await get_payment_by_id(async_session, payment.id)

    assert updated.retry_count == 2


@pytest.mark.asyncio
async def test_payment_with_failure_type(async_session):
    """Test creating payment with failure type."""
    merchant_id = str(uuid4())

    payment = await create_payment(
        async_session,
        merchant_id=merchant_id,
        amount_cents=5000,
        status="failed",
        failure_type="insufficient_funds",
    )

    assert payment.status == "failed"
    assert payment.failure_type == "insufficient_funds"


@pytest.mark.asyncio
async def test_filter_payments_limit(async_session):
    """Test that filter_payments respects limit."""
    merchant_id = str(uuid4())

    # Create 10 payments
    for i in range(10):
        await create_payment(
            async_session, merchant_id=merchant_id, amount_cents=1000 * (i + 1)
        )

    payments = await filter_payments(async_session, limit=5)

    assert len(payments) == 5
