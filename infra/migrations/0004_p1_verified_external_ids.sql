-- Source-attested external identifiers prevent accidental CIK/ticker mixups.
ALTER TABLE ingestion_job ADD COLUMN IF NOT EXISTS company_id INTEGER REFERENCES company(id);
-- Existing job rows have no company identity and are unusable.
-- This is a new table in the P1 rollout; only enforce NOT NULL when empty.
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM ingestion_job WHERE company_id IS NULL) THEN
    RAISE EXCEPTION 'Unattributed ingestion jobs exist: resolve before enforcing company_id';
  END IF;
END $$;
ALTER TABLE ingestion_job ALTER COLUMN company_id SET NOT NULL;

CREATE TABLE IF NOT EXISTS external_identifier (
  id SERIAL PRIMARY KEY,
  company_id INTEGER NOT NULL REFERENCES company(id),
  provider VARCHAR(120) NOT NULL,
  provider_company_id VARCHAR(80) NOT NULL,
  source_snapshot_id INTEGER NOT NULL REFERENCES source_snapshot(id),
  verified_at TIMESTAMP NOT NULL,
  CONSTRAINT uq_external_provider_id UNIQUE (provider, provider_company_id),
  CONSTRAINT uq_company_provider UNIQUE (company_id, provider)
);
