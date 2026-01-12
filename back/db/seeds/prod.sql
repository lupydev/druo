-- ============================================
-- Production Seeds
-- Run ONCE after initial deploy
-- psql $DATABASE_URL -f db/seeds/prod.sql
-- ============================================

-- Create production merchant(s)
-- Replace with real merchant data
INSERT INTO merchants (id, name, email) VALUES 
    ('466fd34b-96a1-4635-9b2c-dedd2645291f', 'DRUO Production', 'payments@druo.com')
ON CONFLICT (id) DO UPDATE SET 
    name = EXCLUDED.name,
    email = EXCLUDED.email,
    updated_at = NOW();

-- Default retry configuration for production
INSERT INTO merchant_retry_configs (
    merchant_id,
    retry_enabled,
    max_attempts,
    insufficient_funds_enabled,
    insufficient_funds_delay,
    card_declined_enabled,
    card_declined_delay,
    network_timeout_enabled,
    network_timeout_delay,
    processor_downtime_enabled,
    processor_downtime_delay
) VALUES (
    '466fd34b-96a1-4635-9b2c-dedd2645291f',
    true,
    3,
    true,
    1440,  -- 24 hours for insufficient funds
    true,
    60,    -- 1 hour for card declined
    true,
    5,     -- 5 minutes for network timeout
    true,
    30     -- 30 minutes for processor downtime
)
ON CONFLICT (merchant_id) DO UPDATE SET
    retry_enabled = EXCLUDED.retry_enabled,
    max_attempts = EXCLUDED.max_attempts,
    updated_at = NOW();

SELECT 'Production seeds loaded!' as status;
