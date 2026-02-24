-- Migration 014: Create api_keys table
-- API key management for external integrations and widget embedding

CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key_hash VARCHAR(255) NOT NULL UNIQUE,          -- bcrypt hash of the actual key (never store plaintext)
    key_prefix VARCHAR(20),                         -- First 8 chars of key for display (e.g., "ragqa_1ab...")
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
    name VARCHAR(255) NOT NULL,                     -- Human-readable name (e.g., "culture.gov.in-widget")
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ,                         -- Null = no expiration, otherwise key becomes invalid
    last_used_at TIMESTAMPTZ,
    last_used_ip VARCHAR(45),
    request_count INT NOT NULL DEFAULT 0,           -- Total requests made with this key
    revoked_at TIMESTAMPTZ,                         -- If revoked before expiration
    revoked_by UUID REFERENCES users(id) ON DELETE SET NULL,
    revocation_reason TEXT,
    metadata JSONB,                                 -- Flexible storage: allowed_ips, domains, rate_limit_override, etc.
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for efficient lookups
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_role_id ON api_keys(role_id);
CREATE INDEX idx_api_keys_is_active ON api_keys(is_active);
CREATE INDEX idx_api_keys_created_by ON api_keys(created_by);
CREATE INDEX idx_api_keys_expires_at ON api_keys(expires_at);
CREATE INDEX idx_api_keys_last_used_at ON api_keys(last_used_at);
CREATE INDEX idx_api_keys_created_at ON api_keys(created_at);

-- Partial index for active non-expired keys
CREATE INDEX idx_api_keys_valid ON api_keys(key_hash) WHERE is_active = true AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP);

-- Add comments for clarity
COMMENT ON TABLE api_keys IS 'API key management for external integrations and embedded chat widget authentication';
COMMENT ON COLUMN api_keys.key_hash IS 'bcrypt hash of the API key (plaintext key shown only to user at creation)';
COMMENT ON COLUMN api_keys.key_prefix IS 'First 8 characters of key, used for display and identification';
COMMENT ON COLUMN api_keys.is_active IS 'Logical deletion flag; false = key is disabled';
COMMENT ON COLUMN api_keys.revoked_at IS 'If set, key has been revoked and is no longer valid (separate from expiration)';
COMMENT ON COLUMN api_keys.metadata IS 'JSONB: flexible storage for allowed_ips, allowed_domains, rate_limit_override, etc.';
