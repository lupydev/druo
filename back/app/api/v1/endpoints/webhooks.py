"""
Webhook endpoints - Callbacks from n8n workflow.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.database import SessionDep
from app.models.audit_log import RetryAuditLog
from app.models.payment import Payment, PaymentStatus
from app.models.retry_job import RetryJob, RetryJobStatus

router = APIRouter()


class RetryResultPayload(BaseModel):
    """Payload from n8n when a retry attempt completes."""

    payment_id: UUID
    attempt_number: int
    success: bool
    result_code: Optional[str] = None
    result_message: Optional[str] = None


@router.post("/retry-result")
async def receive_retry_result(
    payload: RetryResultPayload,
    session: SessionDep,
):
    """
    Receive retry result from n8n workflow.
    Called by n8n after executing a retry attempt.
    """
    # Get the payment
    payment = await session.get(Payment, payload.payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    # Update retry job
    from sqlmodel import select

    result = await session.exec(
        select(RetryJob)
        .where(RetryJob.payment_id == payload.payment_id)
        .where(RetryJob.attempt_number == payload.attempt_number)
    )
    job = result.one_or_none()

    if job:
        job.status = (
            RetryJobStatus.COMPLETED if payload.success else RetryJobStatus.FAILED
        )
        job.executed_at = datetime.now()
        job.result_code = payload.result_code
        job.result_message = payload.result_message
        session.add(job)

    # Update payment status
    if payload.success:
        payment.status = PaymentStatus.RECOVERED
        payment.recovered_via_retry = True
        event_type = "retry_success"
    else:
        payment.retry_count += 1
        payment.last_retry_at = datetime.now()

        # Check if exhausted
        from app.models.retry_config import MerchantRetryConfig

        config_result = await session.exec(
            select(MerchantRetryConfig).where(
                MerchantRetryConfig.merchant_id == payment.merchant_id
            )
        )
        config = config_result.one_or_none()
        max_attempts = config.max_attempts if config else 3

        if payment.retry_count >= max_attempts:
            payment.status = PaymentStatus.EXHAUSTED
            event_type = "exhausted"
        else:
            payment.status = PaymentStatus.RETRYING
            event_type = "retry_failed"

    session.add(payment)

    # Create audit log
    audit_log = RetryAuditLog(
        event_type=event_type,
        payment_id=payload.payment_id,
        merchant_id=payment.merchant_id,
        attempt_number=payload.attempt_number,
        failure_type=payment.failure_type,
        result="success" if payload.success else "failure",
        card_last4=payment.card_last4,
        amount_cents=payment.amount_cents,
        currency=payment.currency,
        metadata_json={
            "result_code": payload.result_code,
            "result_message": payload.result_message,
        },
    )
    session.add(audit_log)

    await session.commit()

    return {
        "status": "received",
        "payment_id": str(payload.payment_id),
        "new_payment_status": payment.status.value,
        "event_logged": event_type,
    }
