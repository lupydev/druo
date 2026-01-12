"""
API v1 Router - Main entry point for all API endpoints.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    merchants,
    payments,
    retry_config,
    retry_logic,
    simulation,
    webhooks,
)

router = APIRouter()

# Include all endpoint routers
router.include_router(merchants.router, prefix="/merchants", tags=["Merchants"])

router.include_router(payments.router, prefix="/payments", tags=["Payments"])

router.include_router(
    retry_config.router, prefix="/retry-config", tags=["Retry Configuration"]
)

router.include_router(
    retry_logic.router, prefix="/retry-logic", tags=["Retry Logic (called by n8n)"]
)

router.include_router(
    webhooks.router, prefix="/webhooks", tags=["Webhooks (n8n callbacks)"]
)

router.include_router(
    simulation.router, prefix="/simulate", tags=["Simulation & Testing"]
)
