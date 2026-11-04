-- Durable authenticated screening presets.
CREATE TABLE IF NOT EXISTS screening_preset (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(120) NOT NULL,
  name VARCHAR(120) NOT NULL,
  filters_json TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_screening_preset_owner_name UNIQUE (user_id, name)
);
CREATE INDEX IF NOT EXISTS ix_screening_preset_owner_id ON screening_preset (user_id, id);
