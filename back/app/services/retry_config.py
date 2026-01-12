from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import select

from app.core.database import SessionDep
from app.models.retry_config import MerchantRetryConfig, RetryConfigUpdate


async def get_config_by_merchant_id(
    session: SessionDep,
    merchant_id: UUID,
) -> MerchantRetryConfig | None:
    """Retrieve retry configuration for a specific merchant."""
    result = await session.exec(
        select(MerchantRetryConfig).where(
            MerchantRetryConfig.merchant_id == merchant_id
        )
    )
    config = result.one_or_none()

    return config


async def update_retry_config_by_merchant_id(
    merchant_id: UUID,
    session: SessionDep,
    config_update: RetryConfigUpdate,
) -> MerchantRetryConfig:
    """Update retry configuration in the database."""
    config = await get_config_by_merchant_id(session, merchant_id)

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Retry config not found for this merchant",
        )
    update_data = config_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)

    session.add(config)
    await session.commit()
    await session.refresh(config)
    return config
