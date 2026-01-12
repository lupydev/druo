from uuid import UUID

from sqlmodel import select

from app.core.database import SessionDep
from app.models.merchant import Merchant, MerchantCreate


async def get_merchant_by_id(session: SessionDep, merchant_id: UUID) -> Merchant | None:
    """Get a specific merchant by ID."""
    merchant = await session.get(Merchant, merchant_id)
    return merchant


async def get_all_merchants(session: SessionDep):
    """List all merchants."""
    result = await session.exec(select(Merchant))
    merchants = result.all()
    return merchants


async def merchant_create(session: SessionDep, merchant_in: MerchantCreate) -> Merchant:
    """Create a new merchant."""
    merchant = Merchant.model_validate(merchant_in)
    session.add(merchant)
    await session.commit()
    await session.refresh(merchant)
    return merchant
