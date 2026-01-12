-- ============================================
-- Database Schema for Payment Retry System
-- This file contains ONLY structure (DDL)
-- ============================================

-- Extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create enum types
DO $$ BEGIN
    CREATE TYPE payment_status AS ENUM ('pending', 'succeeded', 'failed', 'retrying', 'recovered', 'exhausted');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE failure_type AS ENUM ('insufficient_funds', 'card_declined', 'network_timeout', 'processor_downtime', 'fraud', 'expired', 'unknown');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE retry_status AS ENUM ('pending', 'processing', 'completed', 'failed', 'cancelled');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- ============================================
-- Merchants Table
-- ============================================
CREATE TABLE IF NOT EXISTS merchants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- Merchant Retry Configuration
-- ============================================
CREATE TABLE IF NOT EXISTS merchant_retry_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    merchant_id UUID NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,
    
    -- Global settings
    retry_enabled BOOLEAN DEFAULT true,
    max_attempts INTEGER DEFAULT 3 CHECK (max_attempts BETWEEN 1 AND 10),
    
    -- Failure type specific settings (minutes)
    insufficient_funds_enabled BOOLEAN DEFAULT true,
    insufficient_funds_delay INTEGER DEFAULT 1440,  -- 24 hours
    
    card_declined_enabled BOOLEAN DEFAULT true,
    card_declined_delay INTEGER DEFAULT 60,  -- 1 hour
    
    network_timeout_enabled BOOLEAN DEFAULT true,
    network_timeout_delay INTEGER DEFAULT 0,  -- immediate
    
    processor_downtime_enabled BOOLEAN DEFAULT true,
    processor_downtime_delay INTEGER DEFAULT 30,  -- 30 minutes
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(merchant_id)
);

-- ============================================
-- Payments Table
-- ============================================
CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    merchant_id UUID NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,
    
    -- Payment details
    amount_cents BIGINT NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    description VARCHAR(500),
    
    -- Card info (tokenized - no sensitive data)
    card_last4 VARCHAR(4),
    card_brand VARCHAR(20),
    card_fingerprint VARCHAR(100),
    
    -- Status tracking
    status payment_status DEFAULT 'pending',
    failure_type failure_type,
    failure_code VARCHAR(100),
    failure_message TEXT,
    
    -- Retry tracking
    retry_count INTEGER DEFAULT 0,
    last_retry_at TIMESTAMP,
    recovered_via_retry BOOLEAN DEFAULT false,
    
    -- Processor info
    processor VARCHAR(50) DEFAULT 'stripe',
    processor_payment_id VARCHAR(255),
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- Retry Jobs Table
-- ============================================
CREATE TABLE IF NOT EXISTS retry_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    payment_id UUID NOT NULL REFERENCES payments(id) ON DELETE CASCADE,
    merchant_id UUID NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,
    
    attempt_number INTEGER NOT NULL,
    failure_type failure_type NOT NULL,
    
    -- Scheduling
    scheduled_at TIMESTAMP NOT NULL,
    executed_at TIMESTAMP,
    
    -- Status
    status retry_status DEFAULT 'pending',
    result_code VARCHAR(100),
    result_message TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(payment_id, attempt_number)
);

-- ============================================
-- Retry Audit Log (for compliance)
-- ============================================
CREATE TABLE IF NOT EXISTS retry_audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    event_type VARCHAR(50) NOT NULL,
    
    payment_id UUID REFERENCES payments(id) ON DELETE SET NULL,
    merchant_id UUID REFERENCES merchants(id) ON DELETE SET NULL,
    
    attempt_number INTEGER,
    failure_type failure_type,
    result VARCHAR(20),
    
    -- Non-sensitive details
    card_last4 VARCHAR(4),
    amount_cents BIGINT,
    currency VARCHAR(3),
    
    -- Additional context (JSON)
    metadata JSONB,
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- Indexes for Performance
-- ============================================
CREATE INDEX IF NOT EXISTS idx_payments_merchant ON payments(merchant_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
CREATE INDEX IF NOT EXISTS idx_retry_jobs_scheduled ON retry_jobs(scheduled_at) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_retry_jobs_payment ON retry_jobs(payment_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_payment ON retry_audit_logs(payment_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_merchant ON retry_audit_logs(merchant_id, created_at);

SELECT 'Schema created successfully!' as status;
