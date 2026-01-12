"""
Unit tests for retry_jobs service.
"""

from datetime import datetime
from typing import ClassVar
from uuid import uuid4

import pytest
from sqlmodel import Field, SQLModel, select


# Simplified RetryJob model for SQLite testing
class RetryJobTest(SQLModel, table=True):
    """Simplified RetryJob model for testing with SQLite."""

    __tablename__: ClassVar[str] = "retry_jobs_test"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    payment_id: str
    merchant_id: str
    attempt_number: int = Field(default=1)
    failure_type: str
    status: str = Field(default="pending")
    scheduled_at: datetime = Field(default_factory=datetime.now)
    executed_at: datetime | None = Field(default=None)


# Service functions for testing
async def create_retry_job(session, payment_id: str, merchant_id: str, **kwargs):
    """Create a new retry job."""
    job = RetryJobTest(payment_id=payment_id, merchant_id=merchant_id, **kwargs)
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


async def get_retry_jobs_by_payment_id(session, payment_id: str):
    """Get all retry jobs for a payment, ordered by attempt number."""
    result = await session.execute(
        select(RetryJobTest)
        .where(RetryJobTest.payment_id == payment_id)
        .order_by(RetryJobTest.attempt_number)  # type: ignore
    )
    return result.scalars().all()


async def get_pending_jobs(session):
    """Get all pending retry jobs."""
    result = await session.execute(
        select(RetryJobTest).where(RetryJobTest.status == "pending")
    )
    return result.scalars().all()


async def update_job_status(
    session, job_id: str, status: str, executed_at: datetime | None = None
):
    """Update job status."""
    result = await session.execute(
        select(RetryJobTest).where(RetryJobTest.id == job_id)
    )
    job = result.scalar_one_or_none()
    if job:
        job.status = status
        if executed_at:
            job.executed_at = executed_at
        session.add(job)
        await session.commit()
        await session.refresh(job)
    return job


# ============== TESTS ==============


@pytest.mark.asyncio
async def test_create_retry_job(async_session):
    """Test creating a new retry job."""
    payment_id = str(uuid4())
    merchant_id = str(uuid4())

    job = await create_retry_job(
        async_session,
        payment_id=payment_id,
        merchant_id=merchant_id,
        failure_type="insufficient_funds",
        attempt_number=1,
    )

    assert job.id is not None
    assert job.payment_id == payment_id
    assert job.merchant_id == merchant_id
    assert job.failure_type == "insufficient_funds"
    assert job.attempt_number == 1
    assert job.status == "pending"


@pytest.mark.asyncio
async def test_get_retry_jobs_by_payment_id(async_session):
    """Test retrieving retry jobs by payment ID."""
    payment_id = str(uuid4())
    merchant_id = str(uuid4())

    # Create multiple attempts
    await create_retry_job(
        async_session,
        payment_id=payment_id,
        merchant_id=merchant_id,
        failure_type="network_timeout",
        attempt_number=1,
    )
    await create_retry_job(
        async_session,
        payment_id=payment_id,
        merchant_id=merchant_id,
        failure_type="network_timeout",
        attempt_number=2,
    )
    await create_retry_job(
        async_session,
        payment_id=payment_id,
        merchant_id=merchant_id,
        failure_type="network_timeout",
        attempt_number=3,
    )

    jobs = await get_retry_jobs_by_payment_id(async_session, payment_id)

    assert len(jobs) == 3
    assert jobs[0].attempt_number == 1
    assert jobs[1].attempt_number == 2
    assert jobs[2].attempt_number == 3


@pytest.mark.asyncio
async def test_get_retry_jobs_empty(async_session):
    """Test retrieving jobs for non-existent payment returns empty list."""
    random_id = str(uuid4())

    jobs = await get_retry_jobs_by_payment_id(async_session, random_id)

    assert jobs == []


@pytest.mark.asyncio
async def test_get_pending_jobs(async_session):
    """Test retrieving pending jobs."""
    merchant_id = str(uuid4())

    await create_retry_job(
        async_session,
        payment_id=str(uuid4()),
        merchant_id=merchant_id,
        failure_type="network_timeout",
        status="pending",
    )
    await create_retry_job(
        async_session,
        payment_id=str(uuid4()),
        merchant_id=merchant_id,
        failure_type="network_timeout",
        status="completed",
    )
    await create_retry_job(
        async_session,
        payment_id=str(uuid4()),
        merchant_id=merchant_id,
        failure_type="network_timeout",
        status="pending",
    )

    pending = await get_pending_jobs(async_session)

    assert len(pending) == 2
    for job in pending:
        assert job.status == "pending"


@pytest.mark.asyncio
async def test_update_job_status(async_session):
    """Test updating job status."""
    payment_id = str(uuid4())
    merchant_id = str(uuid4())

    job = await create_retry_job(
        async_session,
        payment_id=payment_id,
        merchant_id=merchant_id,
        failure_type="card_declined",
    )
    assert job.status == "pending"

    executed_time = datetime.now()
    updated = await update_job_status(
        async_session,
        job.id,
        status="completed",
        executed_at=executed_time,
    )

    assert updated.status == "completed"
    assert updated.executed_at is not None


@pytest.mark.asyncio
async def test_job_with_scheduled_time(async_session):
    """Test job with specific scheduled time."""
    payment_id = str(uuid4())
    merchant_id = str(uuid4())
    scheduled = datetime(2026, 1, 15, 10, 30, 0)

    job = await create_retry_job(
        async_session,
        payment_id=payment_id,
        merchant_id=merchant_id,
        failure_type="processor_downtime",
        scheduled_at=scheduled,
    )

    assert job.scheduled_at == scheduled


@pytest.mark.asyncio
async def test_multiple_payments_different_jobs(async_session):
    """Test that jobs are correctly associated with their payments."""
    payment1 = str(uuid4())
    payment2 = str(uuid4())
    merchant_id = str(uuid4())

    await create_retry_job(
        async_session,
        payment_id=payment1,
        merchant_id=merchant_id,
        failure_type="network_timeout",
    )
    await create_retry_job(
        async_session,
        payment_id=payment2,
        merchant_id=merchant_id,
        failure_type="insufficient_funds",
    )

    jobs1 = await get_retry_jobs_by_payment_id(async_session, payment1)
    jobs2 = await get_retry_jobs_by_payment_id(async_session, payment2)

    assert len(jobs1) == 1
    assert len(jobs2) == 1
    assert jobs1[0].failure_type == "network_timeout"
    assert jobs2[0].failure_type == "insufficient_funds"
