-- Seed data: Sample documents for testing
-- These documents represent typical ingested Ministry of Culture content

INSERT INTO documents (
    id, title, source_url, source_site, content_type, language,
    document_status, minio_path, chunk_count, metadata
) VALUES
    (
        '550e8400-e29b-41d4-a716-446655440100'::UUID,
        'About the Ministry of Culture',
        'https://culture.gov.in/about-us',
        'culture.gov.in',
        'webpage',
        'hi',
        'completed',
        'documents/processed/550e8400-e29b-41d4-a716-446655440100.txt',
        5,
        '{"published_date": "2024-01-15", "author": "Ministry of Culture", "tags": ["ministry", "about"]}'::JSONB
    ),
    (
        '550e8400-e29b-41d4-a716-446655440101'::UUID,
        'UNESCO World Heritage Sites in India',
        'https://asi.nic.in/monuments/world-heritage-sites',
        'asi.nic.in',
        'webpage',
        'en',
        'completed',
        'documents/processed/550e8400-e29b-41d4-a716-446655440101.txt',
        8,
        '{"published_date": "2024-02-20", "author": "ASI", "tags": ["heritage", "monuments", "unesco"]}'::JSONB
    ),
    (
        '550e8400-e29b-41d4-a716-446655440102'::UUID,
        'Indian Classical Dance Forms',
        'https://culture.gov.in/classical-arts/dance',
        'culture.gov.in',
        'webpage',
        'hi',
        'completed',
        'documents/processed/550e8400-e29b-41d4-a716-446655440102.txt',
        6,
        '{"published_date": "2024-03-10", "author": "Ministry of Culture", "tags": ["arts", "dance", "classical"]}'::JSONB
    ),
    (
        '550e8400-e29b-41d4-a716-446655440103'::UUID,
        'Ancient Indian Literature and Manuscripts',
        'https://nai.nic.in/collections',
        'nai.nic.in',
        'webpage',
        'en',
        'completed',
        'documents/processed/550e8400-e29b-41d4-a716-446655440103.txt',
        10,
        '{"published_date": "2024-01-30", "author": "National Archives of India", "tags": ["literature", "manuscripts", "history"]}'::JSONB
    ),
    (
        '550e8400-e29b-41d4-a716-446655440104'::UUID,
        'Indian Music Tradition and Instruments',
        'https://sangeetnatak.gov.in/music',
        'sangeetnatak.gov.in',
        'webpage',
        'hi',
        'completed',
        'documents/processed/550e8400-e29b-41d4-a716-446655440104.txt',
        7,
        '{"published_date": "2024-02-15", "author": "Sangeet Natak Akademi", "tags": ["music", "tradition", "instruments"]}'::JSONB
    )
ON CONFLICT DO NOTHING;

-- Insert corresponding document chunks for search
INSERT INTO document_chunks (document_id, chunk_index, content, milvus_collection, embedding_status) VALUES
    ('550e8400-e29b-41d4-a716-446655440100'::UUID, 0, 'The Ministry of Culture is responsible for the preservation and promotion of Indian cultural heritage.', 'ministry_text', 'embedded'),
    ('550e8400-e29b-41d4-a716-446655440100'::UUID, 1, 'It works to protect monuments, archaeological sites, and intangible cultural heritage.', 'ministry_text', 'embedded'),
    ('550e8400-e29b-41d4-a716-446655440101'::UUID, 0, 'India has 42 UNESCO World Heritage Sites recognized for their outstanding universal value.', 'ministry_text', 'embedded'),
    ('550e8400-e29b-41d4-a716-446655440101'::UUID, 1, 'These sites include the Taj Mahal, the Great Wall of India, and many ancient temples.', 'ministry_text', 'embedded'),
    ('550e8400-e29b-41d4-a716-446655440102'::UUID, 0, 'Indian classical dance forms include Bharatanatyam, Odissi, Kathak, Kathakali, and others.', 'ministry_text', 'embedded'),
    ('550e8400-e29b-41d4-a716-446655440103'::UUID, 0, 'The National Archives of India preserve millions of documents relating to Indian history.', 'ministry_text', 'embedded'),
    ('550e8400-e29b-41d4-a716-446655440104'::UUID, 0, 'Indian classical music has two major traditions: Hindustani and Carnatic.', 'ministry_text', 'embedded')
ON CONFLICT DO NOTHING;
