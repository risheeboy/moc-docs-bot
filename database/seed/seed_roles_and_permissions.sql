-- Seed data: Initialize RBAC roles and permissions
-- This file seeds the four primary roles (admin, editor, viewer, api_consumer) and their permissions

-- Disable duplicate key constraint during seeding
INSERT INTO roles (id, name, description) VALUES
    ('550e8400-e29b-41d4-a716-446655440001'::UUID, 'admin', 'Full system access including configuration and user management'),
    ('550e8400-e29b-41d4-a716-446655440002'::UUID, 'editor', 'Content management, document ingestion, analytics access'),
    ('550e8400-e29b-41d4-a716-446655440003'::UUID, 'viewer', 'Read-only access to analytics and conversation history'),
    ('550e8400-e29b-41d4-a716-446655440004'::UUID, 'api_consumer', 'API access for chatbot widget and search functionality')
ON CONFLICT (name) DO NOTHING;

-- Admin permissions (full access)
INSERT INTO permissions (role_id, resource, action, description) VALUES
    ('550e8400-e29b-41d4-a716-446655440001'::UUID, 'users', 'create', 'Create new admin users'),
    ('550e8400-e29b-41d4-a716-446655440001'::UUID, 'users', 'read', 'View all users'),
    ('550e8400-e29b-41d4-a716-446655440001'::UUID, 'users', 'update', 'Update user profiles and roles'),
    ('550e8400-e29b-41d4-a716-446655440001'::UUID, 'users', 'delete', 'Delete users'),

    ('550e8400-e29b-41d4-a716-446655440001'::UUID, 'documents', 'create', 'Upload and ingest documents'),
    ('550e8400-e29b-41d4-a716-446655440001'::UUID, 'documents', 'read', 'View all documents'),
    ('550e8400-e29b-41d4-a716-446655440001'::UUID, 'documents', 'update', 'Edit document metadata'),
    ('550e8400-e29b-41d4-a716-446655440001'::UUID, 'documents', 'delete', 'Delete documents'),

    ('550e8400-e29b-41d4-a716-446655440001'::UUID, 'scrape_jobs', 'create', 'Create scraping jobs'),
    ('550e8400-e29b-41d4-a716-446655440001'::UUID, 'scrape_jobs', 'read', 'View scrape job status'),
    ('550e8400-e29b-41d4-a716-446655440001'::UUID, 'scrape_jobs', 'update', 'Pause/resume/cancel scrape jobs'),
    ('550e8400-e29b-41d4-a716-446655440001'::UUID, 'scrape_jobs', 'delete', 'Delete scrape jobs'),

    ('550e8400-e29b-41d4-a716-446655440001'::UUID, 'analytics', 'read', 'View analytics dashboard'),
    ('550e8400-e29b-41d4-a716-446655440001'::UUID, 'analytics', 'export', 'Export analytics data'),

    ('550e8400-e29b-41d4-a716-446655440001'::UUID, 'models', 'create', 'Start model training jobs'),
    ('550e8400-e29b-41d4-a716-446655440001'::UUID, 'models', 'read', 'View model versions'),
    ('550e8400-e29b-41d4-a716-446655440001'::UUID, 'models', 'update', 'Approve/deploy models'),
    ('550e8400-e29b-41d4-a716-446655440001'::UUID, 'models', 'delete', 'Delete model versions'),

    ('550e8400-e29b-41d4-a716-446655440001'::UUID, 'system_config', 'create', 'Create config entries'),
    ('550e8400-e29b-41d4-a716-446655440001'::UUID, 'system_config', 'read', 'View all configuration'),
    ('550e8400-e29b-41d4-a716-446655440001'::UUID, 'system_config', 'update', 'Update system configuration'),
    ('550e8400-e29b-41d4-a716-446655440001'::UUID, 'system_config', 'delete', 'Delete config entries'),

    ('550e8400-e29b-41d4-a716-446655440001'::UUID, 'api_keys', 'create', 'Generate API keys'),
    ('550e8400-e29b-41d4-a716-446655440001'::UUID, 'api_keys', 'read', 'View all API keys'),
    ('550e8400-e29b-41d4-a716-446655440001'::UUID, 'api_keys', 'update', 'Update API key settings'),
    ('550e8400-e29b-41d4-a716-446655440001'::UUID, 'api_keys', 'delete', 'Revoke API keys'),

    ('550e8400-e29b-41d4-a716-446655440001'::UUID, 'audit_log', 'read', 'View audit logs'),
    ('550e8400-e29b-41d4-a716-446655440001'::UUID, 'audit_log', 'export', 'Export audit logs for compliance'),

    ('550e8400-e29b-41d4-a716-446655440001'::UUID, 'roles', 'read', 'View role definitions'),
    ('550e8400-e29b-41d4-a716-446655440001'::UUID, 'permissions', 'read', 'View permissions'),

-- Editor permissions (content management)
    ('550e8400-e29b-41d4-a716-446655440002'::UUID, 'documents', 'create', 'Upload and ingest documents'),
    ('550e8400-e29b-41d4-a716-446655440002'::UUID, 'documents', 'read', 'View all documents'),
    ('550e8400-e29b-41d4-a716-446655440002'::UUID, 'documents', 'update', 'Edit document metadata'),
    ('550e8400-e29b-41d4-a716-446655440002'::UUID, 'documents', 'delete', 'Delete documents'),

    ('550e8400-e29b-41d4-a716-446655440002'::UUID, 'scrape_jobs', 'create', 'Create scraping jobs'),
    ('550e8400-e29b-41d4-a716-446655440002'::UUID, 'scrape_jobs', 'read', 'View scrape job status'),
    ('550e8400-e29b-41d4-a716-446655440002'::UUID, 'scrape_jobs', 'update', 'Pause/resume/cancel scrape jobs'),

    ('550e8400-e29b-41d4-a716-446655440002'::UUID, 'analytics', 'read', 'View analytics dashboard'),
    ('550e8400-e29b-41d4-a716-446655440002'::UUID, 'feedback', 'read', 'View user feedback'),

    ('550e8400-e29b-41d4-a716-446655440002'::UUID, 'events', 'create', 'Create events'),
    ('550e8400-e29b-41d4-a716-446655440002'::UUID, 'events', 'read', 'View events'),
    ('550e8400-e29b-41d4-a716-446655440002'::UUID, 'events', 'update', 'Update events'),
    ('550e8400-e29b-41d4-a716-446655440002'::UUID, 'events', 'delete', 'Delete events'),

-- Viewer permissions (read-only analytics)
    ('550e8400-e29b-41d4-a716-446655440003'::UUID, 'analytics', 'read', 'View analytics dashboard'),
    ('550e8400-e29b-41d4-a716-446655440003'::UUID, 'conversations', 'read', 'Browse conversation history'),
    ('550e8400-e29b-41d4-a716-446655440003'::UUID, 'feedback', 'read', 'View user feedback'),
    ('550e8400-e29b-41d4-a716-446655440003'::UUID, 'events', 'read', 'View events'),
    ('550e8400-e29b-41d4-a716-446655440003'::UUID, 'documents', 'read', 'View documents'),

-- API Consumer permissions (widget/search access)
    ('550e8400-e29b-41d4-a716-446655440004'::UUID, 'chat', 'create', 'Submit chat queries'),
    ('550e8400-e29b-41d4-a716-446655440004'::UUID, 'chat', 'read', 'Retrieve chat responses'),
    ('550e8400-e29b-41d4-a716-446655440004'::UUID, 'search', 'read', 'Perform semantic search'),
    ('550e8400-e29b-41d4-a716-446655440004'::UUID, 'voice', 'create', 'Upload audio for transcription'),
    ('550e8400-e29b-41d4-a716-446655440004'::UUID, 'voice', 'read', 'Retrieve transcription/TTS'),
    ('550e8400-e29b-41d4-a716-446655440004'::UUID, 'translate', 'create', 'Request translations'),
    ('550e8400-e29b-41d4-a716-446655440004'::UUID, 'translate', 'read', 'Retrieve translations'),
    ('550e8400-e29b-41d4-a716-446655440004'::UUID, 'feedback', 'create', 'Submit feedback'),
    ('550e8400-e29b-41d4-a716-446655440004'::UUID, 'ocr', 'create', 'Upload files for OCR'),
    ('550e8400-e29b-41d4-a716-446655440004'::UUID, 'ocr', 'read', 'Retrieve OCR results')
ON CONFLICT (role_id, resource, action) DO NOTHING;
