-- P0 safeguard migration. Run once before deploying the corresponding API.
-- Existing/demo facts stay in the database for audit, but are NOT verified because
-- the new provenance columns default to NULL. Never backfill guessed provenance.
ALTER TABLE financial_statement
    ADD COLUMN IF NOT EXISTS source_url TEXT,
    ADD COLUMN IF NOT EXISTS reporting_currency VARCHAR(3),
    ADD COLUMN IF NOT EXISTS amount_unit VARCHAR(20),
    ADD COLUMN IF NOT EXISTS published_date DATE,
    ADD COLUMN IF NOT EXISTS retrieved_at TIMESTAMP;

-- Old scores were hardcoded. New research snapshots must never claim
-- complete valuation or risk scoring before validated models exist.
ALTER TABLE insight ALTER COLUMN quality_score DROP NOT NULL;
ALTER TABLE insight ALTER COLUMN growth_score DROP NOT NULL;
ALTER TABLE insight ALTER COLUMN valuation_score DROP NOT NULL;
ALTER TABLE insight ALTER COLUMN balance_sheet_score DROP NOT NULL;
ALTER TABLE insight ALTER COLUMN risk_score DROP NOT NULL;
ALTER TABLE insight ALTER COLUMN overall_score DROP NOT NULL;

-- Legacy rows are excluded from the application API until they are
-- replaced by explicitly verified reports.
ALTER TABLE insight
    ADD COLUMN IF NOT EXISTS analysis_status VARCHAR(32),
    ADD COLUMN IF NOT EXISTS evidence_json TEXT,
    ADD COLUMN IF NOT EXISTS source_snapshot_id VARCHAR(120);

-- Clear only identifiers matching the exact old demo generator.
-- Keep legitimate identifiers and all company rows intact.
UPDATE company c
SET isin = ''
FROM country co
WHERE c.country_id = co.id
  AND c.isin = co.iso_code || c.ticker || '0000';

-- Historical mock/seed financial rows are intentionally retained for audit.
-- Their missing provenance keeps them out of research APIs.
-- Legacy insights remain in the database but are hidden by analysis_status.
