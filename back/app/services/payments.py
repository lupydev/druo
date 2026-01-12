from uuid import UUID

from sqlmodel import select

from app.core.database import SessionDep
from app.models.payment import Payment


async def filter_payments(
    session: SessionDep,
    merchant_id: UUID | None = None,
    status: str | None = None,
    limit: int = 50,
):
    query = select(Payment)

    if merchant_id:
        query = query.where(Payment.merchant_id == merchant_id)
    if status:
        query = query.where(Payment.status == status)

    query = query.order_by(Payment.created_at.desc()).limit(limit)  # type: ignore

    result = await session.exec(query)
    payments = result.all()
    return payments


async def get_payment_by_id(session: SessionDep, payment_id: UUID) -> Payment | None:
    """Retrieve a payment by its ID."""

    return await session.get(Payment, payment_id)
