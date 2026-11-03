-- P1: company is an issuer, not a globally unique exchange symbol.
-- SecurityListing(mic, symbol, valid_from) owns tradeable symbol identity.
ALTER TABLE company DROP CONSTRAINT IF EXISTS company_ticker_key;
CREATE INDEX IF NOT EXISTS ix_company_ticker ON company(ticker);

-- FX corrections must be versioned and auditable, not overwritten.
ALTER TABLE fx_observation ADD COLUMN IF NOT EXISTS revision VARCHAR(80) NOT NULL DEFAULT 'original';
ALTER TABLE fx_observation DROP CONSTRAINT IF EXISTS uq_fx_observation;
ALTER TABLE fx_observation
  ADD CONSTRAINT uq_fx_observation
  UNIQUE(provider, observed_date, base_currency, quote_currency, revision);
