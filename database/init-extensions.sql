-- Initialize PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;           -- Full-text search and string similarity
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";       -- UUID generation functions
CREATE EXTENSION IF NOT EXISTS pgcrypto;          -- Cryptographic functions for secure password hashing
