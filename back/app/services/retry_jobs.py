from uuid import UUID

from sqlmodel import select

from app.core.database import SessionDep
from app.models.retry_job import RetryJob


async def get_retry_job_by_payment_id(session: SessionDep, payment_id: UUID):
    """Retrieve a RetryJob by payment ID and attempt number."""

    jobs_result = await session.exec(
        select(RetryJob)
        .where(RetryJob.payment_id == payment_id)
        .order_by(RetryJob.attempt_number)  # type: ignore
    )
    jobs = jobs_result.all()

    return jobs
