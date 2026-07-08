CREATE TABLE IF NOT EXISTS country (
  id SERIAL PRIMARY KEY,
  name VARCHAR(120) NOT NULL UNIQUE,
  iso_code VARCHAR(3) NOT NULL UNIQUE,
  currency_code VARCHAR(3) NOT NULL,
  region VARCHAR(60) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sector (
  id SERIAL PRIMARY KEY,
  name VARCHAR(120) NOT NULL UNIQUE,
  description TEXT NOT NULL DEFAULT '',
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS industry (
  id SERIAL PRIMARY KEY,
  sector_id INTEGER NOT NULL REFERENCES sector(id),
  name VARCHAR(120) NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS company (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  ticker VARCHAR(20) NOT NULL UNIQUE,
  isin VARCHAR(20) NOT NULL DEFAULT '',
  exchange VARCHAR(120) NOT NULL,
  country_id INTEGER NOT NULL REFERENCES country(id),
  sector_id INTEGER NOT NULL REFERENCES sector(id),
  industry_id INTEGER NOT NULL REFERENCES industry(id),
  currency_code VARCHAR(3) NOT NULL,
  website_url VARCHAR(255) NOT NULL DEFAULT '',
  investor_relations_url VARCHAR(255) NOT NULL DEFAULT '',
  description TEXT NOT NULL DEFAULT '',
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS financial_statement (
  id SERIAL PRIMARY KEY,
  company_id INTEGER NOT NULL REFERENCES company(id),
  period_type VARCHAR(12) NOT NULL,
  fiscal_year INTEGER NOT NULL,
  fiscal_quarter INTEGER,
  period_end_date DATE NOT NULL,
  revenue NUMERIC(20,2) NOT NULL,
  gross_profit NUMERIC(20,2) NOT NULL,
  operating_income NUMERIC(20,2) NOT NULL,
  net_income NUMERIC(20,2) NOT NULL,
  total_assets NUMERIC(20,2) NOT NULL,
  total_liabilities NUMERIC(20,2) NOT NULL,
  total_equity NUMERIC(20,2) NOT NULL,
  cash_and_equivalents NUMERIC(20,2) NOT NULL,
  total_debt NUMERIC(20,2) NOT NULL,
  operating_cash_flow NUMERIC(20,2) NOT NULL,
  capital_expenditure NUMERIC(20,2) NOT NULL,
  free_cash_flow NUMERIC(20,2) NOT NULL,
  source VARCHAR(120) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS valuation_metric (
  id SERIAL PRIMARY KEY,
  company_id INTEGER NOT NULL REFERENCES company(id),
  date DATE NOT NULL,
  market_cap NUMERIC(20,2),
  enterprise_value NUMERIC(20,2),
  pe_ratio NUMERIC(12,4),
  forward_pe_ratio NUMERIC(12,4),
  price_to_book NUMERIC(12,4),
  price_to_sales NUMERIC(12,4),
  ev_to_ebitda NUMERIC(12,4),
  dividend_yield NUMERIC(12,4),
  free_cash_flow_yield NUMERIC(12,4),
  source VARCHAR(120) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS market_price (
  id SERIAL PRIMARY KEY,
  company_id INTEGER NOT NULL REFERENCES company(id),
  date DATE NOT NULL,
  open NUMERIC(20,4),
  high NUMERIC(20,4),
  low NUMERIC(20,4),
  close NUMERIC(20,4),
  adjusted_close NUMERIC(20,4),
  volume BIGINT,
  source VARCHAR(120) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS company_document (
  id SERIAL PRIMARY KEY,
  company_id INTEGER NOT NULL REFERENCES company(id),
  document_type VARCHAR(60) NOT NULL,
  title VARCHAR(255) NOT NULL,
  period VARCHAR(50),
  source_url TEXT,
  storage_path TEXT,
  extracted_text_path TEXT,
  published_date DATE,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS insight (
  id SERIAL PRIMARY KEY,
  company_id INTEGER NOT NULL REFERENCES company(id),
  date DATE NOT NULL,
  quality_score FLOAT NOT NULL,
  growth_score FLOAT NOT NULL,
  valuation_score FLOAT NOT NULL,
  balance_sheet_score FLOAT NOT NULL,
  risk_score FLOAT NOT NULL,
  overall_score FLOAT NOT NULL,
  summary TEXT NOT NULL,
  thesis TEXT NOT NULL,
  risks TEXT NOT NULL,
  opportunities TEXT NOT NULL,
  questions_for_further_research TEXT NOT NULL DEFAULT '[]',
  source_snapshot_id VARCHAR(120),
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS risk_flag (
  id SERIAL PRIMARY KEY,
  company_id INTEGER NOT NULL REFERENCES company(id),
  risk_type VARCHAR(80) NOT NULL,
  severity VARCHAR(20) NOT NULL,
  title VARCHAR(255) NOT NULL,
  description TEXT NOT NULL,
  evidence TEXT NOT NULL,
  source VARCHAR(120) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS watchlist (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(120) NOT NULL,
  name VARCHAR(120) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS watchlist_item (
  id SERIAL PRIMARY KEY,
  watchlist_id INTEGER NOT NULL REFERENCES watchlist(id),
  company_id INTEGER NOT NULL REFERENCES company(id),
  notes TEXT,
  target_price NUMERIC(20,4),
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
