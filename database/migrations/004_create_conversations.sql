-- Migration 004: Create conversations (message history) table
-- Stores all user and assistant messages within sessions

CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,                    -- 'user' or 'assistant'
    content TEXT NOT NULL,
    language VARCHAR(10) NOT NULL DEFAULT 'en',   -- Language of message content
    model_used VARCHAR(100),                       -- Which LLM model generated this response
    tokens_used INT,                               -- Token count for this message
    confidence_score FLOAT,                        -- Confidence of RAG retrieval (0.0-1.0)
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for efficient lookups
CREATE INDEX idx_conversations_session_id ON conversations(session_id);
CREATE INDEX idx_conversations_role ON conversations(role);
CREATE INDEX idx_conversations_language ON conversations(language);
CREATE INDEX idx_conversations_created_at ON conversations(created_at);

-- Add comment for clarity
COMMENT ON TABLE conversations IS 'Message history for each session, storing user queries and assistant responses';
COMMENT ON COLUMN conversations.language IS 'ISO 639-1 two-letter language code';
COMMENT ON COLUMN conversations.confidence_score IS 'RAG confidence (0.0-1.0); below threshold triggers fallback response';
