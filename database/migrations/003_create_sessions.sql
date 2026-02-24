-- Migration 003: Create sessions table
-- Tracks chat sessions from users

CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_ip VARCHAR(45),                          -- IPv4 or IPv6
    user_agent TEXT,
    language VARCHAR(10) NOT NULL DEFAULT 'en',   -- ISO 639-1 language code
    is_widget_session BOOLEAN DEFAULT true,        -- true = embedded widget, false = standalone
    session_start_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    session_end_at TIMESTAMPTZ,
    last_activity_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    message_count INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for efficient lookups
CREATE INDEX idx_sessions_language ON sessions(language);
CREATE INDEX idx_sessions_session_start_at ON sessions(session_start_at);
CREATE INDEX idx_sessions_last_activity_at ON sessions(last_activity_at);
CREATE INDEX idx_sessions_is_widget_session ON sessions(is_widget_session);

-- Add comment for clarity
COMMENT ON TABLE sessions IS 'Chat session tracking from both embedded widget and standalone pages';
COMMENT ON COLUMN sessions.language IS 'ISO 639-1 two-letter language code (hi, en, bn, te, mr, ta, ur, gu, kn, ml, or, pa, as, mai, sa, ne, sd, kok, doi, mni, sat, bo, ks)';
