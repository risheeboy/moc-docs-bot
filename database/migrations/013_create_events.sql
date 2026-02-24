-- Migration 013: Create events table
-- Cultural events extracted from Ministry websites for search page event cards

CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    event_date DATE,
    event_date_end DATE,                            -- For multi-day events
    start_time TIME,
    end_time TIME,
    venue VARCHAR(500),
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100) DEFAULT 'India',
    source_url VARCHAR(2048),
    source_site VARCHAR(255) NOT NULL,              -- e.g., "culture.gov.in"
    language VARCHAR(10) NOT NULL DEFAULT 'en',     -- ISO 639-1 language code
    event_type VARCHAR(50),                         -- 'festival', 'conference', 'exhibition', 'workshop', etc.
    organizer VARCHAR(255),
    registration_required BOOLEAN,
    registration_url VARCHAR(2048),
    location_coordinates POINT,                     -- Latitude, longitude for mapping
    thumbnail_image_url VARCHAR(2048),
    metadata JSONB,                                 -- Flexible storage: category, keywords, cost, etc.
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL, -- Source document reference
    last_updated_at TIMESTAMPTZ,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for efficient lookups and searching
CREATE INDEX idx_events_event_date ON events(event_date);
CREATE INDEX idx_events_source_site ON events(source_site);
CREATE INDEX idx_events_language ON events(language);
CREATE INDEX idx_events_event_type ON events(event_type);
CREATE INDEX idx_events_city ON events(city);
CREATE INDEX idx_events_state ON events(state);
CREATE INDEX idx_events_created_at ON events(created_at);
CREATE INDEX idx_events_document_id ON events(document_id);

-- Partial index for upcoming events
CREATE INDEX idx_events_upcoming ON events(event_date) WHERE event_date >= CURRENT_DATE;

-- Add comments for clarity
COMMENT ON TABLE events IS 'Cultural events extracted from Ministry websites for display on search page event cards';
COMMENT ON COLUMN events.language IS 'ISO 639-1 two-letter language code';
COMMENT ON COLUMN events.event_type IS 'Category of event: festival, conference, exhibition, workshop, seminar, webinar, etc.';
COMMENT ON COLUMN events.location_coordinates IS 'Geographic coordinates (latitude, longitude) for mapping';
COMMENT ON COLUMN events.metadata IS 'JSONB: flexible storage for keywords, cost, capacity, registration_deadline, etc.';
