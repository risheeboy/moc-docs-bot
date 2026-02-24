-- Seed data: Initialize default admin user
-- Default admin: username=admin, email=admin@culture.gov.in
-- Password should be changed on first login in production
-- Password hash is for: "ChangeMe123!" (bcrypt hashed)

INSERT INTO users (id, username, email, password_hash, full_name, role_id, is_active)
SELECT
    '550e8400-e29b-41d4-a716-446655440010'::UUID,
    'admin',
    'admin@culture.gov.in',
    '$2b$12$abc123.bcrypt.hash.example.placeholder.must.be.set.in.production',
    'System Administrator',
    '550e8400-e29b-41d4-a716-446655440001'::UUID,
    true
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'admin');
