-- Migration 001: Create roles and permissions tables
-- These tables define the RBAC (Role-Based Access Control) model for the system

CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    resource VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_role_resource_action UNIQUE(role_id, resource, action)
);

-- Create indexes for efficient lookups
CREATE INDEX idx_permissions_role_id ON permissions(role_id);
CREATE INDEX idx_permissions_resource_action ON permissions(resource, action);

-- Add comment for clarity
COMMENT ON TABLE roles IS 'RBAC role definitions: admin, editor, viewer, api_consumer';
COMMENT ON TABLE permissions IS 'Granular permissions per role with resource and action pairing';
