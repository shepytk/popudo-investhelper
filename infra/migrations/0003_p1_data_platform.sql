-- P1: additive, versioned and non-destructive data model.
-- Legacy company.ticker remains unique for compatibility; listings have their
-- own identity and exchange-scoped symbol history. No invented identifiers.

CREATE TABLE IF NOT EXISTS source_snapshot (
  id SERIAL PRIMARY KEY,
  provider VARCHAR(120) NOT NULL,
  source_url TEXT NOT NULL,
  provider_document_id VARCHAR(255) NOT NULL,
  content_hash VARCHAR(64) NOT NULL,
  object_key TEXT NOT NULL,
  published_at TIMESTAMP,
  retrieved_at TIMESTAMP NOT NULL,
  content_type VARCHAR(100) NOT NULL,
  CONSTRAINT uq_source_content_version UNIQUE (provider, provider_document_id, content_hash)
);
CREATE INDEX IF NOT EXISTS ix_snapshot_provider_date ON source_snapshot(provider, retrieved_at);

ALTER TABLE financial_statement
  ADD COLUMN IF NOT EXISTS source_snapshot_id INTEGER REFERENCES source_snapshot(id);

CREATE TABLE IF NOT EXISTS security (
  id SERIAL PRIMARY KEY,
  company_id INTEGER NOT NULL REFERENCES company(id),
  security_type VARCHAR(20) NOT NULL,
  share_class VARCHAR(40) NOT NULL DEFAULT '',
  isin VARCHAR(12) UNIQUE,
  isin_verified BOOLEAN NOT NULL DEFAULT FALSE,
  identifier_source VARCHAR(120),
  identifier_source_url TEXT,
  verified_at TIMESTAMP,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  CONSTRAINT ck_security_verified_evidence
    CHECK (isin_verified = false OR (isin IS NOT NULL AND identifier_source IS NOT NULL AND identifier_source_url IS NOT NULL AND verified_at IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS ix_security_company ON security(company_id);

CREATE TABLE IF NOT EXISTS security_listing (
  id SERIAL PRIMARY KEY,
  security_id INTEGER NOT NULL REFERENCES security(id),
  mic VARCHAR(4) NOT NULL,
  symbol VARCHAR(30) NOT NULL,
  currency_code VARCHAR(3) NOT NULL,
  is_adr BOOLEAN NOT NULL DEFAULT FALSE,
  valid_from DATE NOT NULL,
  valid_to DATE,
  source_snapshot_id INTEGER REFERENCES source_snapshot(id),
  verified BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_listing_mic_symbol_from UNIQUE (mic, symbol, valid_from),
  CONSTRAINT ck_listing_dates CHECK (valid_to IS NULL OR valid_to >= valid_from),
  CONSTRAINT ck_listing_source CHECK (verified = false OR source_snapshot_id IS NOT NULL)
);
CREATE INDEX IF NOT EXISTS ix_listing_symbol_mic ON security_listing(symbol, mic);

CREATE TABLE IF NOT EXISTS symbol_alias (
  id SERIAL PRIMARY KEY,
  listing_id INTEGER NOT NULL REFERENCES security_listing(id),
  symbol VARCHAR(30) NOT NULL,
  valid_from DATE NOT NULL,
  valid_to DATE,
  source_snapshot_id INTEGER NOT NULL REFERENCES source_snapshot(id),
  CONSTRAINT uq_symbol_alias UNIQUE (listing_id, symbol, valid_from)
);

CREATE TABLE IF NOT EXISTS financial_fact (
  id SERIAL PRIMARY KEY,
  company_id INTEGER NOT NULL REFERENCES company(id),
  source_snapshot_id INTEGER NOT NULL REFERENCES source_snapshot(id),
  provider VARCHAR(120) NOT NULL,
  provider_fact_id VARCHAR(255) NOT NULL,
  filing_version VARCHAR(80) NOT NULL,
  concept VARCHAR(100) NOT NULL,
  period_type VARCHAR(12) NOT NULL,
  period_start DATE,
  period_end DATE NOT NULL,
  fiscal_year INTEGER NOT NULL,
  fiscal_quarter INTEGER,
  raw_value NUMERIC(28,8) NOT NULL,
  raw_unit VARCHAR(20) NOT NULL,
  normalized_value NUMERIC(28,8) NOT NULL,
  currency_code VARCHAR(3) NOT NULL,
  reported_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_fact_provider_version UNIQUE (company_id, provider, provider_fact_id, filing_version)
);
CREATE INDEX IF NOT EXISTS ix_fact_company_period ON financial_fact(company_id, concept, period_end);

CREATE TABLE IF NOT EXISTS quote_observation (
  id SERIAL PRIMARY KEY,
  listing_id INTEGER NOT NULL REFERENCES security_listing(id),
  source_snapshot_id INTEGER NOT NULL REFERENCES source_snapshot(id),
  provider VARCHAR(120) NOT NULL,
  session_date DATE NOT NULL,
  revision VARCHAR(80) NOT NULL DEFAULT 'original',
  close NUMERIC(28,8) NOT NULL,
  currency_code VARCHAR(3) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_quote_version UNIQUE (listing_id, provider, session_date, revision)
);

CREATE TABLE IF NOT EXISTS fx_observation (
  id SERIAL PRIMARY KEY,
  source_snapshot_id INTEGER NOT NULL REFERENCES source_snapshot(id),
  provider VARCHAR(120) NOT NULL,
  observed_date DATE NOT NULL,
  base_currency VARCHAR(3) NOT NULL,
  quote_currency VARCHAR(3) NOT NULL,
  rate NUMERIC(28,12) NOT NULL,
  CONSTRAINT uq_fx_observation UNIQUE (provider, observed_date, base_currency, quote_currency),
  CONSTRAINT ck_fx_positive_rate CHECK (rate > 0)
);

CREATE TABLE IF NOT EXISTS ingestion_job (
  id SERIAL PRIMARY KEY,
  provider VARCHAR(120) NOT NULL,
  subject VARCHAR(255) NOT NULL,
  state VARCHAR(24) NOT NULL DEFAULT 'pending',
  attempts INTEGER NOT NULL DEFAULT 0,
  max_attempts INTEGER NOT NULL DEFAULT 3,
  last_error TEXT,
  next_run_at TIMESTAMP NOT NULL,
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_ingestion_queue ON ingestion_job(state, next_run_at);

-- Search paths must remain bounded and sortable.
CREATE INDEX IF NOT EXISTS ix_company_name_id ON company(name, id);
CREATE INDEX IF NOT EXISTS ix_company_country_sector ON company(country_id, sector_id);
CREATE INDEX IF NOT EXISTS ix_statement_company_period ON financial_statement(company_id, period_end_date DESC);
