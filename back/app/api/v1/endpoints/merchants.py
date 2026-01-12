from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.core.database import SessionDep
from app.models.merchant import MerchantCreate, MerchantRead
from app.services.merchants import (
    get_all_merchants,
    get_merchant_by_id,
    merchant_create,
)

router = APIRouter()


@router.get("/", response_model=list[MerchantRead])
async def list_merchants(session: SessionDep):
    """List all merchants."""
    return await get_all_merchants(session)


@router.get("/{merchant_id}", response_model=MerchantRead)
async def get_merchant(merchant_id: UUID, session: SessionDep):
    """Get a specific merchant by ID."""
    merchant = await get_merchant_by_id(session, merchant_id)

    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Merchant not found"
        )
    return merchant


@router.post("/", response_model=MerchantRead)
async def create_merchant(merchant_in: MerchantCreate, session: SessionDep):
    """Create a new merchant."""
    return await merchant_create(session, merchant_in)
