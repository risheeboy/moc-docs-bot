-- Migration 010: Create scrape_jobs table
-- Tracks web scraping jobs and their status

CREATE TABLE IF NOT EXISTS scrape_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    target_url VARCHAR(2048) NOT NULL,
    source_site VARCHAR(255) NOT NULL,              -- e.g., "culture.gov.in", "asi.nic.in"
    spider_type VARCHAR(50) NOT NULL DEFAULT 'auto', -- 'auto', 'sitemap', 'breadth-first', 'depth-first'
    job_status VARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed', 'paused'
    last_scraped_at TIMESTAMPTZ,
    pages_crawled INT NOT NULL DEFAULT 0,
    pages_failed INT NOT NULL DEFAULT 0,
    documents_ingested INT NOT NULL DEFAULT 0,
    error_message TEXT,                             -- Last error encountered, if any
    scheduled_frequency_hours INT,                  -- Null = manual only, otherwise run every N hours
    next_scheduled_at TIMESTAMPTZ,
    last_scheduled_job_id UUID,                     -- Reference to last scheduled job
    triggered_by UUID REFERENCES users(id) ON DELETE SET NULL, -- User who manually triggered this
    metadata JSONB,                                 -- Flexible storage: robots_txt_compliant, sitemap_url, etc.
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for efficient lookups
CREATE INDEX idx_scrape_jobs_source_site ON scrape_jobs(source_site);
CREATE INDEX idx_scrape_jobs_target_url ON scrape_jobs(target_url);
CREATE INDEX idx_scrape_jobs_job_status ON scrape_jobs(job_status);
CREATE INDEX idx_scrape_jobs_last_scraped_at ON scrape_jobs(last_scraped_at);
CREATE INDEX idx_scrape_jobs_next_scheduled_at ON scrape_jobs(next_scheduled_at);
CREATE INDEX idx_scrape_jobs_created_at ON scrape_jobs(created_at);

-- Partial index for scheduled jobs
CREATE INDEX idx_scrape_jobs_scheduled ON scrape_jobs(next_scheduled_at) WHERE job_status != 'failed';

-- Add comments for clarity
COMMENT ON TABLE scrape_jobs IS 'Web scraping job tracking for Ministry website content ingestion';
COMMENT ON COLUMN scrape_jobs.job_status IS 'Current job status: pending → running → completed (or failed or paused)';
COMMENT ON COLUMN scrape_jobs.spider_type IS 'Strategy used by Scrapy spider: auto (intelligent), sitemap, breadth-first, or depth-first';
COMMENT ON COLUMN scrape_jobs.metadata IS 'JSONB: flexible storage for robots_txt_compliant, sitemap_url, cookie_handling, etc.';
