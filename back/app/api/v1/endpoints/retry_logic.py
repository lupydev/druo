"""
Retry Logic endpoints - Core retry processing logic.
These endpoints are called by n8n to execute the retry logic in Python.
"""

import random
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlmodel import select

from app.core.database import SessionDep
from app.models.audit_log import RetryAuditLog
from app.models.payment import FailureType, PaymentStatus
from app.models.retry_config import MerchantRetryConfig
from app.services.payments import get_payment_by_id
from app.services.retry_config import get_config_by_merchant_id

router = APIRouter()


# ============================================
# Request/Response Models
# ============================================


class ClassifyFailureRequest(BaseModel):
    """Request to classify a payment failure."""

    payment_id: UUID
    failure_type: FailureType
    merchant_id: UUID


class ClassifyFailureResponse(BaseModel):
    """Response from failure classification."""

    payment_id: UUID
    failure_type: str
    is_retriable: bool
    reason: str
    retry_enabled: bool
    delay_minutes: int
    max_attempts: int


class ExecuteRetryRequest(BaseModel):
    """Request to execute a retry attempt."""

    payment_id: UUID
    merchant_id: UUID
    attempt_number: int
    failure_type: str


class ExecuteRetryResponse(BaseModel):
    """Response from retry execution."""

    payment_id: UUID
    attempt_number: int
    success: bool
    result_code: str
    result_message: str
    success_probability: float
    random_value: float
    should_continue: bool
    next_attempt: Optional[int]


class UpdatePaymentStatusRequest(BaseModel):
    """Request to update payment status after retry."""

    payment_id: UUID
    attempt_number: int
    success: bool
    result_code: str
    result_message: str


# ============================================
# Success rates by failure type (from PRD)
# ============================================

SUCCESS_RATES = {
    FailureType.INSUFFICIENT_FUNDS: 0.20,  # 20% success
    FailureType.CARD_DECLINED: 0.15,  # 15% success
    FailureType.NETWORK_TIMEOUT: 0.60,  # 60% success
    FailureType.PROCESSOR_DOWNTIME: 0.80,  # 80% success
    FailureType.UNKNOWN: 0.10,  # 10% success
    FailureType.FRAUD: 0.0,  # Never succeeds (non-retriable)
    FailureType.EXPIRED: 0.0,  # Never succeeds (non-retriable)
}

# Non-retriable failure types
NON_RETRIABLE_TYPES = {FailureType.FRAUD, FailureType.EXPIRED}


# ============================================
# Endpoints
# ============================================


@router.post("/classify", response_model=ClassifyFailureResponse)
async def classify_failure(
    request: ClassifyFailureRequest,
    session: SessionDep,
):
    """
    Classify a payment failure and determine if it should be retried.

    This is called by n8n after receiving a payment failure webhook.
    Returns whether the failure is retriable and the retry configuration.
    """
    # Parse failure type
    try:
        failure_type = FailureType(request.failure_type)
    except ValueError:
        failure_type = FailureType.UNKNOWN

    # Check if failure type is retriable
    is_retriable = failure_type not in NON_RETRIABLE_TYPES

    if not is_retriable:
        return ClassifyFailureResponse(
            payment_id=request.payment_id,
            failure_type=failure_type.value,
            is_retriable=False,
            reason=f"Failure type '{failure_type.value}' is not eligible for retry",
            retry_enabled=False,
            delay_minutes=0,
            max_attempts=0,
        )

    # Get merchant retry configuration
    config = await get_config_by_merchant_id(session, request.merchant_id)

    if not config:
        return ClassifyFailureResponse(
            payment_id=request.payment_id,
            failure_type=failure_type.value,
            is_retriable=False,
            reason="Merchant retry configuration not found",
            retry_enabled=False,
            delay_minutes=0,
            max_attempts=0,
        )

    # Check if retry is enabled globally
    if not config.retry_enabled:
        return ClassifyFailureResponse(
            payment_id=request.payment_id,
            failure_type=failure_type.value,
            is_retriable=True,
            reason="Retry is disabled for this merchant",
            retry_enabled=False,
            delay_minutes=0,
            max_attempts=0,
        )

    # Check if retry is enabled for this specific failure type
    failure_type_enabled_field = f"{failure_type.value}_enabled"
    failure_type_delay_field = f"{failure_type.value}_delay"

    is_enabled_for_type = getattr(config, failure_type_enabled_field, False)
    delay_minutes = getattr(config, failure_type_delay_field, 60)

    if not is_enabled_for_type:
        return ClassifyFailureResponse(
            payment_id=request.payment_id,
            failure_type=failure_type.value,
            is_retriable=True,
            reason=f"Retry is disabled for failure type '{failure_type.value}'",
            retry_enabled=False,
            delay_minutes=0,
            max_attempts=0,
        )

    # Log classification
    audit_log = RetryAuditLog(
        event_type="classified",
        payment_id=request.payment_id,
        merchant_id=request.merchant_id,
        failure_type=failure_type,
        metadata_json={
            "is_retriable": True,
            "delay_minutes": delay_minutes,
            "max_attempts": config.max_attempts,
        },
    )
    session.add(audit_log)
    await session.commit()

    return ClassifyFailureResponse(
        payment_id=request.payment_id,
        failure_type=failure_type.value,
        is_retriable=True,
        reason="Failure is eligible for retry",
        retry_enabled=True,
        delay_minutes=delay_minutes,
        max_attempts=config.max_attempts,
    )


@router.post("/execute", response_model=ExecuteRetryResponse)
async def execute_retry(
    request: ExecuteRetryRequest,
    session: SessionDep,
):
    """
    Execute a retry attempt for a payment.

    This simulates calling the payment processor to retry the payment.
    In production, this would call Stripe/PSE/Nequi APIs.
    Returns whether the retry succeeded and if more attempts should be made.
    """
    # Parse failure type
    try:
        failure_type = FailureType(request.failure_type)
    except ValueError:
        failure_type = FailureType.UNKNOWN

    # Get success probability for this failure type
    success_probability = SUCCESS_RATES.get(failure_type, 0.10)

    # Simulate the retry - random success based on probability
    random_value = random.random()
    success = random_value < success_probability

    # Get merchant config for max attempts
    result = await session.exec(
        select(MerchantRetryConfig).where(
            MerchantRetryConfig.merchant_id == request.merchant_id
        )
    )
    config = result.one_or_none()
    max_attempts = config.max_attempts if config else 3

    # Determine if we should continue retrying
    should_continue = not success and request.attempt_number < max_attempts
    next_attempt = request.attempt_number + 1 if should_continue else None

    # Prepare result
    if success:
        result_code = "succeeded"
        result_message = (
            f"Payment recovered successfully on attempt {request.attempt_number}"
        )
    else:
        result_code = failure_type.value
        result_message = (
            f"Retry attempt {request.attempt_number} failed: {failure_type.value}"
        )
        if not should_continue:
            result_message += " (all attempts exhausted)"

    # Log the retry attempt
    audit_log = RetryAuditLog(
        event_type="retry_executed",
        payment_id=request.payment_id,
        merchant_id=request.merchant_id,
        attempt_number=request.attempt_number,
        failure_type=failure_type,
        result="success" if success else "failure",
        metadata_json={
            "success_probability": success_probability,
            "random_value": random_value,
            "should_continue": should_continue,
        },
    )
    session.add(audit_log)
    await session.commit()

    return ExecuteRetryResponse(
        payment_id=request.payment_id,
        attempt_number=request.attempt_number,
        success=success,
        result_code=result_code,
        result_message=result_message,
        success_probability=success_probability,
        random_value=round(random_value, 4),
        should_continue=should_continue,
        next_attempt=next_attempt,
    )


@router.post("/update-status")
async def update_payment_status(
    request: UpdatePaymentStatusRequest,
    session: SessionDep,
):
    """
    Update the payment status after a retry attempt.

    This is called by n8n after the retry result is determined.
    Updates the payment record and creates appropriate audit logs.
    """
    # Get the payment
    payment = await get_payment_by_id(session, request.payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found"
        )

    # Update payment based on result
    if request.success:
        payment.status = PaymentStatus.RECOVERED
        payment.recovered_via_retry = True
        event_type = "retry_success"
    else:
        payment.retry_count = request.attempt_number
        payment.last_retry_at = datetime.now()

        # Check if this was the final attempt
        result = await session.exec(
            select(MerchantRetryConfig).where(
                MerchantRetryConfig.merchant_id == payment.merchant_id
            )
        )
        config = result.one_or_none()
        max_attempts = config.max_attempts if config else 3

        if request.attempt_number >= max_attempts:
            payment.status = PaymentStatus.EXHAUSTED
            event_type = "exhausted"
        else:
            payment.status = PaymentStatus.RETRYING
            event_type = "retry_failed"

    payment.updated_at = datetime.now()
    session.add(payment)

    # Create audit log
    audit_log = RetryAuditLog(
        event_type=event_type,
        payment_id=request.payment_id,
        merchant_id=payment.merchant_id,
        attempt_number=request.attempt_number,
        failure_type=payment.failure_type,
        result="success" if request.success else "failure",
        card_last4=payment.card_last4,
        amount_cents=payment.amount_cents,
        currency=payment.currency,
        metadata_json={
            "result_code": request.result_code,
            "result_message": request.result_message,
        },
    )
    session.add(audit_log)

    await session.commit()
    await session.refresh(payment)

    return {
        "status": "updated",
        "payment_id": str(request.payment_id),
        "new_status": payment.status.value,
        "event_logged": event_type,
        "attempt_number": request.attempt_number,
        "recovered": request.success,
    }


@router.get("/health")
async def retry_logic_health():
    """Health check for retry logic endpoints."""
    return {
        "status": "healthy",
        "service": "retry-logic",
        "success_rates": {k.value: v for k, v in SUCCESS_RATES.items()},
        "non_retriable_types": [t.value for t in NON_RETRIABLE_TYPES],
    }
