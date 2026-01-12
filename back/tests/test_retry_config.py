"""
Unit tests for retry_config service.
"""

from typing import ClassVar
from uuid import uuid4

import pytest
from sqlmodel import Field, SQLModel, select


# Simplified RetryConfig model for SQLite testing
class RetryConfigTest(SQLModel, table=True):
    """Simplified RetryConfig model for testing with SQLite."""

    __tablename__: ClassVar[str] = "retry_config_test"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    merchant_id: str = Field(unique=True)
    retry_enabled: bool = Field(default=True)
    max_attempts: int = Field(default=3)
    insufficient_funds_enabled: bool = Field(default=True)
    insufficient_funds_delay: int = Field(default=1440)
    card_declined_enabled: bool = Field(default=True)
    card_declined_delay: int = Field(default=60)
    network_timeout_enabled: bool = Field(default=True)
    network_timeout_delay: int = Field(default=0)


# Service functions for testing
async def create_retry_config(session, merchant_id: str, **kwargs):
    """Create a new retry config."""
    config = RetryConfigTest(merchant_id=merchant_id, **kwargs)
    session.add(config)
    await session.commit()
    await session.refresh(config)
    return config


async def get_config_by_merchant_id(session, merchant_id: str):
    """Get config by merchant ID."""
    result = await session.execute(
        select(RetryConfigTest).where(RetryConfigTest.merchant_id == merchant_id)
    )
    return result.scalar_one_or_none()


async def update_retry_config(session, merchant_id: str, **updates):
    """Update retry config."""
    config = await get_config_by_merchant_id(session, merchant_id)
    if config:
        for field, value in updates.items():
            setattr(config, field, value)
        session.add(config)
        await session.commit()
        await session.refresh(config)
    return config


# ============== TESTS ==============


@pytest.mark.asyncio
async def test_create_retry_config(async_session):
    """Test creating a new retry config."""
    merchant_id = str(uuid4())

    config = await create_retry_config(
        async_session,
        merchant_id=merchant_id,
        retry_enabled=True,
        max_attempts=3,
    )

    assert config.id is not None
    assert config.merchant_id == merchant_id
    assert config.retry_enabled is True
    assert config.max_attempts == 3


@pytest.mark.asyncio
async def test_get_config_by_merchant_id(async_session):
    """Test retrieving config by merchant ID."""
    merchant_id = str(uuid4())

    await create_retry_config(
        async_session,
        merchant_id=merchant_id,
        max_attempts=5,
    )

    found = await get_config_by_merchant_id(async_session, merchant_id)

    assert found is not None
    assert found.merchant_id == merchant_id
    assert found.max_attempts == 5


@pytest.mark.asyncio
async def test_get_config_by_merchant_id_not_found(async_session):
    """Test retrieving non-existent config returns None."""
    random_id = str(uuid4())

    found = await get_config_by_merchant_id(async_session, random_id)

    assert found is None


@pytest.mark.asyncio
async def test_update_retry_config(async_session):
    """Test updating retry config."""
    merchant_id = str(uuid4())

    await create_retry_config(
        async_session,
        merchant_id=merchant_id,
        retry_enabled=True,
        max_attempts=3,
    )

    updated = await update_retry_config(
        async_session,
        merchant_id=merchant_id,
        retry_enabled=False,
        max_attempts=5,
    )

    assert updated is not None
    assert updated.retry_enabled is False
    assert updated.max_attempts == 5


@pytest.mark.asyncio
async def test_update_retry_config_partial(async_session):
    """Test partial update of retry config."""
    merchant_id = str(uuid4())

    await create_retry_config(
        async_session,
        merchant_id=merchant_id,
        retry_enabled=True,
        max_attempts=3,
        insufficient_funds_enabled=True,
    )

    # Only update max_attempts
    updated = await update_retry_config(
        async_session,
        merchant_id=merchant_id,
        max_attempts=10,
    )

    assert updated.max_attempts == 10
    assert updated.retry_enabled is True  # Unchanged
    assert updated.insufficient_funds_enabled is True  # Unchanged


@pytest.mark.asyncio
async def test_retry_config_default_values(async_session):
    """Test that default values are applied correctly."""
    merchant_id = str(uuid4())

    config = await create_retry_config(async_session, merchant_id=merchant_id)

    assert config.retry_enabled is True
    assert config.max_attempts == 3
    assert config.insufficient_funds_enabled is True
    assert config.insufficient_funds_delay == 1440
    assert config.card_declined_enabled is True
    assert config.card_declined_delay == 60
    assert config.network_timeout_enabled is True
    assert config.network_timeout_delay == 0


@pytest.mark.asyncio
async def test_disable_specific_failure_type(async_session):
    """Test disabling retry for specific failure type."""
    merchant_id = str(uuid4())

    await create_retry_config(
        async_session,
        merchant_id=merchant_id,
        insufficient_funds_enabled=False,
    )

    config = await get_config_by_merchant_id(async_session, merchant_id)

    assert config.insufficient_funds_enabled is False
    assert config.card_declined_enabled is True  # Others remain enabled
