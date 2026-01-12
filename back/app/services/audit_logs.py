from uuid import UUID

from sqlmodel import select

from app.core.database import SessionDep
from app.models.audit_log import RetryAuditLog


async def get_log_audits_by_payment_id(session: SessionDep, payment_id: UUID):
    """Retrieve audit logs for a specific payment ID."""

    logs_result = await session.exec(
        select(RetryAuditLog)
        .where(RetryAuditLog.payment_id == payment_id)
        .order_by(RetryAuditLog.created_at)  # type: ignore
    )
    logs = logs_result.all()

    return logs
