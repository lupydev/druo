"""
Retry Configuration endpoints - Merchant retry settings.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from app.core.database import SessionDep
from app.models.retry_config import (
    MerchantRetryConfig,
    RetryConfigRead,
    RetryConfigUpdate,
)
from app.services.retry_config import (
    get_config_by_merchant_id,
    update_retry_config_by_merchant_id,
)

router = APIRouter()


@router.get("/{merchant_id}", response_model=RetryConfigRead)
async def get_retry_config(
    merchant_id: UUID,
    session: SessionDep,
):
    """Get retry configuration for a merchant."""
    config = await get_config_by_merchant_id(session, merchant_id)

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Retry config not found for this merchant",
        )

    return config


@router.put("/{merchant_id}", response_model=RetryConfigRead)
async def update_retry_config(
    merchant_id: UUID,
    config_update: RetryConfigUpdate,
    session: SessionDep,
):
    """Update retry configuration for a merchant."""

    return await update_retry_config_by_merchant_id(
        merchant_id=merchant_id,
        config_update=config_update,
        session=session,
    )


@router.get("/{merchant_id}/preview")
async def preview_retry_settings(
    merchant_id: UUID,
    session: SessionDep,
):
    """
    Preview what would happen with current retry settings.
    Returns estimated recovery rates based on configuration.
    """
    result = await session.exec(
        select(MerchantRetryConfig).where(
            MerchantRetryConfig.merchant_id == merchant_id
        )
    )
    config = result.one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="Retry config not found")

    # Estimated recovery rates by failure type (from PRD data)
    recovery_rates = {
        "insufficient_funds": {"rate": 0.20, "pct_of_failures": 0.35},
        "card_declined": {"rate": 0.15, "pct_of_failures": 0.25},
        "network_timeout": {"rate": 0.60, "pct_of_failures": 0.20},
        "processor_downtime": {"rate": 0.80, "pct_of_failures": 0.05},
    }

    total_recoverable = 0
    breakdown = []

    for failure_type, data in recovery_rates.items():
        enabled_field = f"{failure_type}_enabled"
        is_enabled = getattr(config, enabled_field, False)

        if is_enabled and config.retry_enabled:
            recoverable = data["rate"] * data["pct_of_failures"] * 100
            total_recoverable += recoverable
            breakdown.append(
                {
                    "failure_type": failure_type,
                    "enabled": True,
                    "estimated_recovery_rate": f"{data['rate'] * 100:.0f}%",
                    "contribution_to_total": f"{recoverable:.1f}%",
                }
            )
        else:
            breakdown.append(
                {
                    "failure_type": failure_type,
                    "enabled": False,
                    "estimated_recovery_rate": "0%",
                    "contribution_to_total": "0%",
                }
            )

    return {
        "merchant_id": str(merchant_id),
        "retry_enabled": config.retry_enabled,
        "max_attempts": config.max_attempts,
        "estimated_total_recovery": f"{total_recoverable:.1f}%",
        "message": f"With these settings, approximately {total_recoverable:.1f}% of failed payments could be recovered",
        "breakdown": breakdown,
    }
