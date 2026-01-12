-- ============================================
-- Development Seeds
-- Run with: psql $DATABASE_URL -f db/seeds/dev.sql
-- ============================================

-- Demo Merchant
INSERT INTO merchants (id, name, email) VALUES 
    ('466fd34b-96a1-4635-9b2c-dedd2645291f', 'Demo Merchant', 'demo@example.com')
ON CONFLICT (id) DO NOTHING;

INSERT INTO merchant_retry_configs (merchant_id) VALUES 
    ('466fd34b-96a1-4635-9b2c-dedd2645291f')
ON CONFLICT (merchant_id) DO NOTHING;

-- Sample failed payments for testing
INSERT INTO payments (merchant_id, amount_cents, currency, card_last4, card_brand, status, failure_type, failure_code, failure_message, processor) VALUES
    ('466fd34b-96a1-4635-9b2c-dedd2645291f', 15000, 'USD', '4242', 'visa', 'failed', 'insufficient_funds', 'insufficient_funds', 'Your card has insufficient funds.', 'stripe'),
    ('466fd34b-96a1-4635-9b2c-dedd2645291f', 25000, 'USD', '5555', 'mastercard', 'failed', 'card_declined', 'card_declined', 'Your card was declined.', 'stripe'),
    ('466fd34b-96a1-4635-9b2c-dedd2645291f', 8000, 'USD', '3782', 'amex', 'failed', 'network_timeout', 'processing_error', 'Network timeout during processing.', 'stripe');

SELECT 'Development seeds loaded!' as status;
