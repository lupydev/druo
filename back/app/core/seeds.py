"""
Database seeding script.
Creates initial data if it doesn't exist.
"""

import asyncio
import random
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.database import engine
from app.models.merchant import Merchant
from app.models.payment import FailureType, Payment, PaymentStatus
from app.models.retry_config import MerchantRetryConfig

DEMO_MERCHANT_ID = UUID("466fd34b-96a1-4635-9b2c-dedd2645291f")

processor = random.choice(["stripe", "dlocal", "pse", "nequi"])

# Sample failed payments for testing
SAMPLE_PAYMENTS = [
    {
        "amount_cents": 15000,
        "currency": "USD",
        "card_last4": "4242",
        "card_brand": "visa",
        "status": PaymentStatus.FAILED,
        "failure_type": FailureType.INSUFFICIENT_FUNDS,
        "failure_code": "insufficient_funds",
        "failure_message": "Your card has insufficient funds.",
        "processor": processor,
    },
    {
        "amount_cents": 25000,
        "currency": "USD",
        "card_last4": "5555",
        "card_brand": "mastercard",
        "status": PaymentStatus.FAILED,
        "failure_type": FailureType.CARD_DECLINED,
        "failure_code": "card_declined",
        "failure_message": "Your card was declined.",
        "processor": processor,
    },
    {
        "amount_cents": 8000,
        "currency": "USD",
        "card_last4": "3782",
        "card_brand": "amex",
        "status": PaymentStatus.FAILED,
        "failure_type": FailureType.NETWORK_TIMEOUT,
        "failure_code": "processing_error",
        "failure_message": "Network timeout during processing.",
        "processor": processor,
    },
]


async def seed_database():
    """Seed the database with initial data."""

    if not settings.DATABASE_URL:
        print("⚠️  DATABASE_URL not set, skipping seeds")
        return

    async with AsyncSession(engine, expire_on_commit=False) as session:
        result = await session.exec(
            select(Merchant).where(Merchant.id == DEMO_MERCHANT_ID)
        )
        existing_merchant = result.one_or_none()

        if existing_merchant:
            print("✅ Seeds already applied (demo merchant exists)")
            return

        if settings.ENVIRONMENT == "production":
            merchant = Merchant(
                id=DEMO_MERCHANT_ID, name="DRUO Production", email="payments@druo.com"
            )
        else:
            merchant = Merchant(
                id=DEMO_MERCHANT_ID, name="Demo Merchant", email="demo@example.com"
            )

        session.add(merchant)
        await session.flush()

        # Create default retry config
        config = MerchantRetryConfig(
            merchant_id=DEMO_MERCHANT_ID,
            retry_enabled=True,
            max_attempts=3,
            insufficient_funds_enabled=True,
            insufficient_funds_delay=1440,
            card_declined_enabled=True,
            card_declined_delay=60,
            network_timeout_enabled=True,
            network_timeout_delay=5,
            processor_downtime_enabled=True,
            processor_downtime_delay=30,
        )

        session.add(config)
        await session.flush()

        # Create sample failed payments (only in development)
        if settings.ENVIRONMENT != "production":
            for payment_data in SAMPLE_PAYMENTS:
                payment = Payment(
                    merchant_id=DEMO_MERCHANT_ID,
                    **payment_data,
                )
                session.add(payment)
            print(f"   Added {len(SAMPLE_PAYMENTS)} sample payments")

        await session.commit()

        print(f"🌱 Seeds applied successfully ({settings.ENVIRONMENT})")


def run_seeds():
    """Entry point for seeding."""
    asyncio.run(seed_database())


if __name__ == "__main__":
    run_seeds()
