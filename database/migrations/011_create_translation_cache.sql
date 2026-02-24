-- Migration 011: Create translation_cache table
-- Caches translations to avoid redundant API calls to IndicTrans2

CREATE TABLE IF NOT EXISTS translation_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_text_hash VARCHAR(64) NOT NULL,          -- SHA-256 hash of source text
    source_language VARCHAR(10) NOT NULL,           -- ISO 639-1 language code
    target_language VARCHAR(10) NOT NULL,           -- ISO 639-1 language code
    source_text TEXT NOT NULL,
    translated_text TEXT NOT NULL,
    confidence_score FLOAT,                         -- Optional: model confidence
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ                          -- TTL for cache expiration
);

-- Create indexes for efficient cache lookups
CREATE UNIQUE INDEX idx_translation_cache_unique ON translation_cache(source_text_hash, source_language, target_language);
CREATE INDEX idx_translation_cache_expires_at ON translation_cache(expires_at);

-- Add comments for clarity
COMMENT ON TABLE translation_cache IS 'Cache of translations from IndicTrans2 service to reduce API calls';
COMMENT ON COLUMN translation_cache.source_text_hash IS 'SHA-256 hash of the original source text for fast lookup';
COMMENT ON COLUMN translation_cache.source_language IS 'ISO 639-1 source language code';
COMMENT ON COLUMN translation_cache.target_language IS 'ISO 639-1 target language code';
COMMENT ON COLUMN translation_cache.expires_at IS 'Expiration timestamp for cache TTL (24 hours default)';
