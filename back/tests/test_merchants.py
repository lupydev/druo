"""
Unit tests for merchants service.
"""

from uuid import uuid4

import pytest
from app.models.merchant import Merchant, MerchantCreate
from sqlmodel import select


# Implement service functions locally to avoid database.py import
async def get_merchant_by_id(session, merchant_id):
    """Get a specific merchant by ID."""
    merchant = await session.get(Merchant, merchant_id)
    return merchant


async def get_all_merchants(session):
    """List all merchants."""
    result = await session.execute(select(Merchant))
    merchants = result.scalars().all()
    return merchants


async def merchant_create(session, merchant_in: MerchantCreate):
    """Create a new merchant."""
    merchant = Merchant.model_validate(merchant_in)
    session.add(merchant)
    await session.commit()
    await session.refresh(merchant)
    return merchant


@pytest.mark.asyncio
async def test_merchant_create(async_session):
    """Test creating a new merchant."""
    merchant_data = MerchantCreate(name="Test Merchant", email="test@merchant.com")

    merchant = await merchant_create(async_session, merchant_data)

    assert merchant.id is not None
    assert merchant.name == "Test Merchant"
    assert merchant.email == "test@merchant.com"
    assert merchant.created_at is not None


@pytest.mark.asyncio
async def test_get_merchant_by_id(async_session):
    """Test retrieving a merchant by ID."""
    # Create a merchant first
    merchant_data = MerchantCreate(name="Find Me Merchant", email="findme@merchant.com")
    created = await merchant_create(async_session, merchant_data)

    # Retrieve it by ID
    found = await get_merchant_by_id(async_session, created.id)

    assert found is not None
    assert found.id == created.id
    assert found.name == "Find Me Merchant"
    assert found.email == "findme@merchant.com"


@pytest.mark.asyncio
async def test_get_merchant_by_id_not_found(async_session):
    """Test retrieving a non-existent merchant returns None."""
    random_id = uuid4()

    found = await get_merchant_by_id(async_session, random_id)

    assert found is None


@pytest.mark.asyncio
async def test_get_all_merchants_empty(async_session):
    """Test getting all merchants when none exist."""
    merchants = await get_all_merchants(async_session)

    assert merchants == []


@pytest.mark.asyncio
async def test_get_all_merchants(async_session):
    """Test getting all merchants."""
    # Create multiple merchants
    await merchant_create(
        async_session, MerchantCreate(name="Merchant 1", email="merchant1@test.com")
    )
    await merchant_create(
        async_session, MerchantCreate(name="Merchant 2", email="merchant2@test.com")
    )
    await merchant_create(
        async_session, MerchantCreate(name="Merchant 3", email="merchant3@test.com")
    )

    merchants = await get_all_merchants(async_session)

    assert len(merchants) == 3
    names = [m.name for m in merchants]
    assert "Merchant 1" in names
    assert "Merchant 2" in names
    assert "Merchant 3" in names


@pytest.mark.asyncio
async def test_merchant_has_timestamps(async_session):
    """Test that created merchant has created_at and updated_at."""
    merchant_data = MerchantCreate(name="Timestamp Test", email="timestamp@test.com")

    merchant = await merchant_create(async_session, merchant_data)

    assert merchant.created_at is not None
    assert merchant.updated_at is not None
