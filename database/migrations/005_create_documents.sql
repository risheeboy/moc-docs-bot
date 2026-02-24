-- Migration 005: Create documents and document_chunks tables
-- Stores metadata for ingested documents and their vector chunks

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    source_url VARCHAR(2048),
    source_site VARCHAR(255) NOT NULL,            -- e.g., "culture.gov.in", "asi.nic.in"
    content_type VARCHAR(50) NOT NULL,             -- 'webpage', 'pdf', 'docx', 'image', etc.
    language VARCHAR(10) NOT NULL DEFAULT 'en',    -- ISO 639-1 language code
    file_size_bytes INT,
    minio_path VARCHAR(500),                       -- Path in MinIO object storage
    chunk_count INT NOT NULL DEFAULT 0,
    document_status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- 'pending', 'processing', 'completed', 'failed'
    processed_at TIMESTAMPTZ,
    indexed_at TIMESTAMPTZ,                        -- When chunks were indexed in Milvus
    last_crawled_at TIMESTAMPTZ,
    metadata JSONB,                                -- Flexible metadata storage (author, published_date, tags, etc.)
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,                      -- Position within document
    content TEXT NOT NULL,
    chunk_tokens INT,
    milvus_collection VARCHAR(100),                -- 'ministry_text' or 'ministry_images'
    milvus_id VARCHAR(100),                        -- ID within Milvus collection
    embedding_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'embedded', 'failed'
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for efficient lookups
CREATE INDEX idx_documents_source_site ON documents(source_site);
CREATE INDEX idx_documents_source_url ON documents(source_url);
CREATE INDEX idx_documents_language ON documents(language);
CREATE INDEX idx_documents_document_status ON documents(document_status);
CREATE INDEX idx_documents_created_at ON documents(created_at);
CREATE INDEX idx_documents_indexed_at ON documents(indexed_at);

CREATE INDEX idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX idx_document_chunks_milvus_id ON document_chunks(milvus_id);
CREATE INDEX idx_document_chunks_embedding_status ON document_chunks(embedding_status);

-- Add comments for clarity
COMMENT ON TABLE documents IS 'Metadata for all ingested documents from Ministry websites';
COMMENT ON COLUMN documents.source_site IS 'Fully qualified domain name (e.g., culture.gov.in, asi.nic.in)';
COMMENT ON COLUMN documents.language IS 'ISO 639-1 two-letter language code';
COMMENT ON COLUMN documents.document_status IS 'Ingestion status: pending → processing → completed (or failed)';
COMMENT ON COLUMN documents.metadata IS 'JSONB object with optional fields: author, published_date, tags, etc.';

COMMENT ON TABLE document_chunks IS 'Individual chunks of documents, vectorized and stored in Milvus';
COMMENT ON COLUMN document_chunks.milvus_collection IS 'Collection name in Milvus (ministry_text for text, ministry_images for images)';
COMMENT ON COLUMN document_chunks.milvus_id IS 'Reference ID in Milvus collection for vector lookup';
