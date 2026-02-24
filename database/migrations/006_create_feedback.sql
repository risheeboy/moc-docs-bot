-- Migration 006: Create feedback table
-- User ratings and feedback on responses, including sentiment analysis

CREATE TABLE IF NOT EXISTS feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    rating INT,                                     -- 1-5 star rating (null = no rating)
    feedback_text TEXT,
    is_helpful BOOLEAN,                             -- Thumbs up/down
    sentiment_score FLOAT,                          -- -1.0 to 1.0 (negative to positive)
    sentiment_label VARCHAR(20),                    -- 'negative', 'neutral', 'positive'
    language VARCHAR(10) NOT NULL DEFAULT 'en',     -- ISO 639-1 language code
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for efficient lookups and analytics
CREATE INDEX idx_feedback_session_id ON feedback(session_id);
CREATE INDEX idx_feedback_conversation_id ON feedback(conversation_id);
CREATE INDEX idx_feedback_rating ON feedback(rating);
CREATE INDEX idx_feedback_is_helpful ON feedback(is_helpful);
CREATE INDEX idx_feedback_sentiment_label ON feedback(sentiment_label);
CREATE INDEX idx_feedback_created_at ON feedback(created_at);

-- Add comments for clarity
COMMENT ON TABLE feedback IS 'User feedback, ratings, and sentiment analysis on chatbot responses';
COMMENT ON COLUMN feedback.rating IS 'Optional star rating (1-5)';
COMMENT ON COLUMN feedback.is_helpful IS 'Boolean: true = helpful (thumbs up), false = not helpful (thumbs down), NULL = no rating';
COMMENT ON COLUMN feedback.sentiment_score IS 'ML-computed sentiment score: -1.0 (very negative) to 1.0 (very positive)';
COMMENT ON COLUMN feedback.sentiment_label IS 'Categorical sentiment: negative, neutral, or positive';
COMMENT ON COLUMN feedback.language IS 'ISO 639-1 two-letter language code of feedback text';
