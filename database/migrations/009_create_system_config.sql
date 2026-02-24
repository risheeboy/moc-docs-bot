-- Migration 009: Create system_config table
-- Key-value store for application configuration, feature flags, and thresholds

CREATE TABLE IF NOT EXISTS system_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    config_key VARCHAR(255) NOT NULL UNIQUE,
    config_value TEXT NOT NULL,
    description TEXT,
    value_type VARCHAR(50) NOT NULL DEFAULT 'string',  -- 'string', 'integer', 'float', 'boolean', 'json'
    is_secret BOOLEAN NOT NULL DEFAULT false,          -- If true, don't expose in logs/APIs
    is_mutable BOOLEAN NOT NULL DEFAULT true,          -- If false, can only be set at initialization
    updated_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create index for fast lookups
CREATE INDEX idx_system_config_key ON system_config(config_key);

-- Add comments for clarity
COMMENT ON TABLE system_config IS 'Global configuration key-value store for thresholds, rate limits, feature flags, and system settings';
COMMENT ON COLUMN system_config.is_secret IS 'If true, value should be masked in logs and API responses';
COMMENT ON COLUMN system_config.is_mutable IS 'If false, configuration is read-only (set once at initialization)';
COMMENT ON COLUMN system_config.value_type IS 'Type of the value for parsing: string, integer, float, boolean, or json';
