-- ============================================
-- Docker Init: Schema + Dev Seeds
-- This file is used by docker-compose for local development
-- ============================================

-- Load schema
\i /docker-entrypoint-initdb.d/schema.sql

-- Load dev seeds
\i /docker-entrypoint-initdb.d/seeds/dev.sql
