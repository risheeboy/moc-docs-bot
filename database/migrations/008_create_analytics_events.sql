-- Migration 008: Create analytics_events table
-- Tracks query analytics and system performance metrics

CREATE TABLE IF NOT EXISTS analytics_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES sessions(id) ON DELETE SET NULL,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    event_type VARCHAR(50) NOT NULL,               -- 'query', 'response', 'rag_retrieval', 'llm_inference', etc.
    language VARCHAR(10),                          -- ISO 639-1 language code of query/response
    model_used VARCHAR(100),                       -- Which model was invoked
    latency_ms INT,                                -- Duration in milliseconds
    tokens_used INT,
    confidence_score FLOAT,
    cache_hit BOOLEAN,
    source_count INT,                              -- Number of sources retrieved by RAG
    metadata JSONB,                                -- Additional metrics (model_version, topic_detected, etc.)
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for efficient analytics queries
CREATE INDEX idx_analytics_events_session_id ON analytics_events(session_id);
CREATE INDEX idx_analytics_events_conversation_id ON analytics_events(conversation_id);
CREATE INDEX idx_analytics_events_event_type ON analytics_events(event_type);
CREATE INDEX idx_analytics_events_language ON analytics_events(language);
CREATE INDEX idx_analytics_events_model_used ON analytics_events(model_used);
CREATE INDEX idx_analytics_events_cache_hit ON analytics_events(cache_hit);
CREATE INDEX idx_analytics_events_created_at ON analytics_events(created_at);

-- Composite index for common time-series queries
CREATE INDEX idx_analytics_events_type_time ON analytics_events(event_type, created_at);

-- Add comments for clarity
COMMENT ON TABLE analytics_events IS 'Performance and usage analytics for all system events';
COMMENT ON COLUMN analytics_events.event_type IS 'Type of event (query, response, rag_retrieval, llm_inference, speech_stt, tts, translation, ocr)';
COMMENT ON COLUMN analytics_events.latency_ms IS 'End-to-end duration of the event in milliseconds';
COMMENT ON COLUMN analytics_events.metadata IS 'JSONB object with event-specific metrics (model_version, input_tokens, output_tokens, etc.)';
