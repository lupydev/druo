"""
Payments endpoints - CRUD and management for payments.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.core.database import SessionDep
from app.models.payment import PaymentRead, PaymentStatus
from app.services.audit_logs import get_log_audits_by_payment_id
from app.services.payments import filter_payments, get_payment_by_id
from app.services.retry_jobs import get_retry_job_by_payment_id

router = APIRouter()


@router.get("/", response_model=List[PaymentRead])
async def list_payments(
    session: SessionDep,
    merchant_id: UUID | None = Query(None, description="Filter by merchant"),
    status: PaymentStatus | None = Query(None, description="Filter by status"),
    limit: int = Query(50, le=100),
):
    """List payments with optional filters."""
    return await filter_payments(
        session=session,
        merchant_id=merchant_id,
        status=status,
        limit=limit,
    )


@router.get("/{payment_id}", response_model=PaymentRead)
async def get_payment(
    payment_id: UUID,
    session: SessionDep,
):
    """Get a specific payment by ID."""
    payment = await get_payment_by_id(session, payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found"
        )
    return payment


@router.get("/{payment_id}/retry-history")
async def get_payment_retry_history(
    payment_id: UUID,
    session: SessionDep,
):
    """Get retry history for a specific payment."""

    # Get retry jobs
    jobs = await get_retry_job_by_payment_id(session, payment_id)

    # Get audit logs
    logs = await get_log_audits_by_payment_id(session, payment_id)

    return {"payment_id": str(payment_id), "retry_jobs": jobs, "audit_logs": logs}
