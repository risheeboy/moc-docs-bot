-- Migration 007: Create audit_log table
-- Tracks all system events for compliance and debugging

CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,                  -- e.g., 'create_document', 'delete_session', 'config_update'
    resource_type VARCHAR(100) NOT NULL,           -- e.g., 'document', 'user', 'session', 'system_config'
    resource_id VARCHAR(255),                      -- ID of the resource affected (could be any type)
    user_ip VARCHAR(45),                           -- IPv4 or IPv6 address
    user_agent TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'success', -- 'success' or 'failure'
    details JSONB,                                 -- Additional context-specific information
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for efficient lookups and compliance queries
CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_action ON audit_log(action);
CREATE INDEX idx_audit_log_resource_type ON audit_log(resource_type);
CREATE INDEX idx_audit_log_resource_id ON audit_log(resource_id);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at);
CREATE INDEX idx_audit_log_user_ip ON audit_log(user_ip);
CREATE INDEX idx_audit_log_status ON audit_log(status);

-- Partial index for failures (common query: show me all failed actions)
CREATE INDEX idx_audit_log_failures ON audit_log(created_at) WHERE status = 'failure';

-- Add comments for clarity
COMMENT ON TABLE audit_log IS 'Immutable audit trail of all system events for compliance and debugging';
COMMENT ON COLUMN audit_log.action IS 'System action type (e.g., document_created, user_deleted, config_changed)';
COMMENT ON COLUMN audit_log.resource_type IS 'Type of resource affected (document, user, session, role, permission, etc.)';
COMMENT ON COLUMN audit_log.resource_id IS 'ID of the affected resource (UUID for most, but can be string for config keys)';
COMMENT ON COLUMN audit_log.details IS 'JSONB object with additional context (old_value, new_value, reason, etc.)';
