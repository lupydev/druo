"""
Simulation endpoints - For testing and demos.
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import select

from app.core.config import settings
from app.core.database import SessionDep
from app.models.audit_log import RetryAuditLog
from app.models.payment import FailureType, Payment, PaymentStatus
from app.models.retry_config import MerchantRetryConfig
from app.models.retry_job import RetryJob, RetryJobStatus

router = APIRouter()


class SimulateFailureRequest(BaseModel):
    """Request to simulate a failed payment."""

    merchant_id: UUID
    amount_cents: int = 10000
    currency: str = "USD"
    failure_type: FailureType = FailureType.INSUFFICIENT_FUNDS
    card_last4: str = "4242"
    processor: str = "stripe"


class SimulateFailureResponse(BaseModel):
    """Response from simulating a failed payment."""

    payment_id: UUID
    status: str
    failure_type: str
    retry_scheduled: bool
    scheduled_at: Optional[datetime] = None
    n8n_triggered: bool
    message: str


@router.post("/failure", response_model=SimulateFailureResponse)
async def simulate_payment_failure(
    request: SimulateFailureRequest,
    session: SessionDep,
):
    """
    Simulate a failed payment and trigger retry workflow.

    This endpoint:
    1. Creates a failed payment in the database
    2. Checks merchant retry configuration
    3. Schedules a retry job if enabled
    4. Triggers the n8n workflow via webhook
    """
    # Get merchant retry config
    config_result = await session.execute(
        select(MerchantRetryConfig).where(
            MerchantRetryConfig.merchant_id == request.merchant_id
        )
    )
    config = config_result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=404,
            detail="Merchant retry configuration not found. Create merchant first.",
        )

    # Create the failed payment
    payment = Payment(
        merchant_id=request.merchant_id,
        amount_cents=request.amount_cents,
        currency=request.currency,
        card_last4=request.card_last4,
        card_brand="visa",
        status=PaymentStatus.FAILED,
        failure_type=request.failure_type,
        failure_code=request.failure_type.value,
        failure_message=f"Simulated failure: {request.failure_type.value}",
        processor=request.processor,
    )
    session.add(payment)
    await session.flush()  # Get the payment ID

    # Log the failure
    audit_log = RetryAuditLog(
        event_type="payment_failed",
        payment_id=payment.id,
        merchant_id=request.merchant_id,
        failure_type=request.failure_type,
        card_last4=request.card_last4,
        amount_cents=request.amount_cents,
        currency=request.currency,
    )
    session.add(audit_log)

    # Check if retry is enabled for this failure type
    retry_enabled_field = f"{request.failure_type.value}_enabled"
    delay_field = f"{request.failure_type.value}_delay"

    should_retry = config.retry_enabled and getattr(config, retry_enabled_field, False)

    retry_scheduled = False
    scheduled_at = None
    n8n_triggered = False

    if should_retry:
        # Calculate delay
        delay_minutes = getattr(config, delay_field, 60)
        scheduled_at = datetime.now() + timedelta(minutes=delay_minutes)

        # Create retry job
        retry_job = RetryJob(
            payment_id=payment.id,
            merchant_id=request.merchant_id,
            attempt_number=1,
            failure_type=request.failure_type,
            scheduled_at=scheduled_at,
            status=RetryJobStatus.PENDING,
        )
        session.add(retry_job)

        # Log scheduling
        schedule_log = RetryAuditLog(
            event_type="retry_scheduled",
            payment_id=payment.id,
            merchant_id=request.merchant_id,
            attempt_number=1,
            failure_type=request.failure_type,
            metadata_json={
                "scheduled_at": scheduled_at.isoformat(),
                "delay_minutes": delay_minutes,
            },
        )
        session.add(schedule_log)

        payment.status = PaymentStatus.RETRYING
        retry_scheduled = True

        # Trigger n8n webhook
        try:
            async with httpx.AsyncClient() as client:
                webhook_url = f"{settings.N8N_WEBHOOK_URL}/payment-failed"
                payload = {
                    "payment_id": str(payment.id),
                    "merchant_id": str(request.merchant_id),
                    "amount_cents": request.amount_cents,
                    "currency": request.currency,
                    "failure_type": request.failure_type.value,
                    "card_last4": request.card_last4,
                    "attempt_number": 1,
                    "scheduled_at": scheduled_at.isoformat(),
                    "delay_minutes": delay_minutes,
                    "max_attempts": config.max_attempts,
                    "callback_url": "http://backend:8000/api/v1/webhooks/retry-result",
                }
                response = await client.post(webhook_url, json=payload, timeout=5.0)
                n8n_triggered = response.status_code == 200
        except Exception as e:
            # Log but don't fail - n8n might not be running
            print(f"Warning: Could not trigger n8n webhook: {e}")
            n8n_triggered = False

    await session.commit()
    await session.refresh(payment)

    return SimulateFailureResponse(
        payment_id=payment.id,
        status=payment.status.value,
        failure_type=request.failure_type.value,
        retry_scheduled=retry_scheduled,
        scheduled_at=scheduled_at,
        n8n_triggered=n8n_triggered,
        message="Retry scheduled"
        if retry_scheduled
        else "Retry not enabled for this failure type",
    )


@router.post("/trigger-retry/{payment_id}")
async def manually_trigger_retry(
    payment_id: UUID,
    session: SessionDep,
):
    """
    Manually trigger a retry for a specific payment.
    Useful for testing the n8n workflow.
    """
    payment = await session.get(Payment, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    # Get config
    config_result = await session.execute(
        select(MerchantRetryConfig).where(
            MerchantRetryConfig.merchant_id == payment.merchant_id
        )
    )
    config = config_result.scalar_one_or_none()

    # Trigger n8n
    try:
        async with httpx.AsyncClient() as client:
            webhook_url = f"{settings.N8N_WEBHOOK_URL}/payment-failed"
            payload = {
                "payment_id": str(payment.id),
                "merchant_id": str(payment.merchant_id),
                "amount_cents": payment.amount_cents,
                "currency": payment.currency,
                "failure_type": payment.failure_type.value
                if payment.failure_type
                else "unknown",
                "card_last4": payment.card_last4,
                "attempt_number": payment.retry_count + 1,
                "max_attempts": config.max_attempts if config else 3,
                "callback_url": "http://backend:8000/api/v1/webhooks/retry-result",
            }
            response = await client.post(webhook_url, json=payload, timeout=5.0)

            return {
                "status": "triggered",
                "payment_id": str(payment_id),
                "n8n_response_status": response.status_code,
                "payload_sent": payload,
            }
    except Exception as e:
        raise HTTPException(
            status_code=503, detail=f"Could not trigger n8n webhook: {str(e)}"
        )


@router.get("/stats/{merchant_id}")
async def get_simulation_stats(
    merchant_id: UUID,
    session: SessionDep,
):
    """Get retry statistics for a merchant."""
    from sqlalchemy import func

    # Count payments by status
    result = await session.exec(
        select(Payment.status, func.count(Payment.id))  # type: ignore
        .where(Payment.merchant_id == merchant_id)
        .group_by(Payment.status)
    )
    status_counts = {row[0].value: row[1] for row in result.all()}  # type: ignore

    # Sum amount_cents for recovered payments
    recovered_amount_result = await session.exec(
        select(func.coalesce(func.sum(Payment.amount_cents), 0))  # type: ignore
        .where(Payment.merchant_id == merchant_id)
        .where(Payment.status == PaymentStatus.RECOVERED)
    )
    recovered_amount = recovered_amount_result.one()

    # Sum amount_cents for retrying payments
    retrying_amount_result = await session.exec(
        select(func.coalesce(func.sum(Payment.amount_cents), 0))  # type: ignore
        .where(Payment.merchant_id == merchant_id)
        .where(
            Payment.status == PaymentStatus.RETRYING,
            Payment.status == PaymentStatus.SUCCEEDED,
        )  # type: ignore
    )
    retrying_amount = retrying_amount_result.one()

    # Sum amount_cents for failed + exhausted payments (lost)
    lost_amount_result = await session.exec(
        select(func.coalesce(func.sum(Payment.amount_cents), 0))  # type: ignore
        .where(Payment.merchant_id == merchant_id)
        .where(Payment.status.in_([PaymentStatus.FAILED, PaymentStatus.EXHAUSTED]))  # type: ignore
    )
    lost_amount = lost_amount_result.one()

    # Count recovered payments
    recovered = status_counts.get("recovered", 0)
    failed = status_counts.get("failed", 0)
    exhausted = status_counts.get("exhausted", 0)
    retrying = status_counts.get("retrying", 0)

    total_eligible = failed + exhausted + recovered + retrying
    recovery_rate = (recovered / total_eligible * 100) if total_eligible > 0 else 0

    return {
        "merchant_id": str(merchant_id),
        "total_payments": sum(status_counts.values()),
        "status_breakdown": status_counts,
        "recovery_rate": f"{recovery_rate:.1f}%",
        "recovered_count": recovered,
        "recovered_amount_cents": recovered_amount,
        "retrying_count": retrying,
        "retrying_amount_cents": retrying_amount,
        "failed_count": failed,
        "exhausted_count": exhausted,
        "lost_amount_cents": lost_amount,
    }
