-- Seed data: System configuration
-- Rate limits, retention periods, model names, and other settings from §3.2 of Shared Contracts

-- Rate Limits (requests per minute per role)
INSERT INTO system_config (config_key, config_value, value_type, description, is_mutable) VALUES
    ('RATE_LIMIT_ADMIN', '120', 'integer', 'Rate limit for admin role (requests/minute)', true),
    ('RATE_LIMIT_EDITOR', '90', 'integer', 'Rate limit for editor role (requests/minute)', true),
    ('RATE_LIMIT_VIEWER', '30', 'integer', 'Rate limit for viewer role (requests/minute)', true),
    ('RATE_LIMIT_API_CONSUMER', '60', 'integer', 'Rate limit for api_consumer role (requests/minute)', true)
ON CONFLICT (config_key) DO NOTHING;

-- Data Retention Policies (days)
INSERT INTO system_config (config_key, config_value, value_type, description, is_mutable) VALUES
    ('RETENTION_CONVERSATIONS_DAYS', '90', 'integer', 'Retention period for conversation history (days)', true),
    ('RETENTION_FEEDBACK_DAYS', '365', 'integer', 'Retention period for feedback data (days)', true),
    ('RETENTION_AUDIT_LOG_DAYS', '730', 'integer', 'Retention period for audit logs (days - 2 years)', true),
    ('RETENTION_ANALYTICS_DAYS', '365', 'integer', 'Retention period for analytics events (days)', true),
    ('RETENTION_TRANSLATION_CACHE_DAYS', '30', 'integer', 'TTL for translation cache entries (days)', true)
ON CONFLICT (config_key) DO NOTHING;

-- LLM Models (from §3.2)
INSERT INTO system_config (config_key, config_value, value_type, description, is_mutable) VALUES
    ('LLM_MODEL_STANDARD', 'meta-llama/Llama-3.1-8B-Instruct-AWQ', 'string', 'Standard LLM model for general queries', true),
    ('LLM_MODEL_LONGCTX', 'mistralai/Mistral-NeMo-Instruct-2407-AWQ', 'string', 'Long-context LLM model for large documents', true),
    ('LLM_MODEL_MULTIMODAL', 'google/gemma-3-12b-it-awq', 'string', 'Multimodal LLM model for image understanding', true),
    ('LLM_GPU_MEMORY_UTILIZATION', '0.85', 'float', 'GPU memory utilization target for vLLM', false),
    ('LLM_MAX_MODEL_LEN_STANDARD', '8192', 'integer', 'Max context length for standard model', false),
    ('LLM_MAX_MODEL_LEN_LONGCTX', '131072', 'integer', 'Max context length for long-context model', false),
    ('LLM_MAX_MODEL_LEN_MULTIMODAL', '8192', 'integer', 'Max context length for multimodal model', false)
ON CONFLICT (config_key) DO NOTHING;

-- RAG Configuration
INSERT INTO system_config (config_key, config_value, value_type, description, is_mutable) VALUES
    ('RAG_EMBEDDING_MODEL', 'BAAI/bge-m3', 'string', 'Multilingual dense+sparse embedding model', false),
    ('RAG_VISION_EMBEDDING_MODEL', 'google/siglip-so400m-patch14-384', 'string', 'Vision embedding model for image search', false),
    ('RAG_CHUNK_SIZE', '512', 'integer', 'Text chunk size for document splitting (tokens)', true),
    ('RAG_CHUNK_OVERLAP', '64', 'integer', 'Overlap between chunks (tokens)', true),
    ('RAG_TOP_K', '10', 'integer', 'Number of top results to retrieve from Milvus', true),
    ('RAG_RERANK_TOP_K', '5', 'integer', 'Number of results after reranking', true),
    ('RAG_CONFIDENCE_THRESHOLD', '0.65', 'float', 'Confidence threshold below which fallback response is used', true),
    ('RAG_CACHE_TTL_SECONDS', '3600', 'integer', 'Query result cache TTL in seconds (1 hour)', true)
ON CONFLICT (config_key) DO NOTHING;

-- Session Configuration
INSERT INTO system_config (config_key, config_value, value_type, description, is_mutable) VALUES
    ('SESSION_IDLE_TIMEOUT_SECONDS', '1800', 'integer', 'Session idle timeout (30 minutes)', true),
    ('SESSION_MAX_TURNS', '50', 'integer', 'Maximum conversation turns before truncation', true),
    ('SESSION_CONTEXT_WINDOW_TOKENS', '4096', 'integer', 'Maximum tokens to keep in context', true)
ON CONFLICT (config_key) DO NOTHING;

-- Translation Service Configuration
INSERT INTO system_config (config_key, config_value, value_type, description, is_mutable) VALUES
    ('TRANSLATION_MODEL', 'ai4bharat/indictrans2-indic-en-1B', 'string', 'IndicTrans2 model for Indian language translation', false),
    ('TRANSLATION_CACHE_TTL_SECONDS', '86400', 'integer', 'Translation cache TTL (24 hours)', true)
ON CONFLICT (config_key) DO NOTHING;

-- Speech Service Configuration
INSERT INTO system_config (config_key, config_value, value_type, description, is_mutable) VALUES
    ('SPEECH_STT_MODEL', 'ai4bharat/indicconformer-hi-en', 'string', 'IndicConformer for speech-to-text', false),
    ('SPEECH_TTS_HINDI_MODEL', 'ai4bharat/indic-tts-hindi', 'string', 'IndicTTS model for Hindi text-to-speech', false),
    ('SPEECH_TTS_ENGLISH_MODEL', 'coqui/tts-english', 'string', 'Coqui TTS for English text-to-speech', false),
    ('SPEECH_SAMPLE_RATE', '16000', 'integer', 'Audio sample rate (Hz)', false)
ON CONFLICT (config_key) DO NOTHING;

-- OCR Configuration
INSERT INTO system_config (config_key, config_value, value_type, description, is_mutable) VALUES
    ('OCR_TESSERACT_LANG', 'hin+eng', 'string', 'Tesseract languages (Hindi + English)', false),
    ('OCR_EASYOCR_LANGS', 'hi,en', 'string', 'EasyOCR languages (Hindi, English)', false)
ON CONFLICT (config_key) DO NOTHING;

-- Data Ingestion Configuration
INSERT INTO system_config (config_key, config_value, value_type, description, is_mutable) VALUES
    ('INGESTION_SCRAPE_INTERVAL_HOURS', '24', 'integer', 'Default scrape interval (hours)', true),
    ('INGESTION_MAX_CONCURRENT_SPIDERS', '4', 'integer', 'Maximum concurrent Scrapy spiders', true),
    ('INGESTION_RESPECT_ROBOTS_TXT', 'true', 'boolean', 'Respect robots.txt when scraping', false)
ON CONFLICT (config_key) DO NOTHING;

-- Feature Flags
INSERT INTO system_config (config_key, config_value, value_type, description, is_mutable) VALUES
    ('FEATURE_VOICE_INPUT', 'true', 'boolean', 'Enable voice input (STT) in chat widget', true),
    ('FEATURE_VOICE_OUTPUT', 'true', 'boolean', 'Enable voice output (TTS) in chat widget', true),
    ('FEATURE_TRANSLATION', 'true', 'boolean', 'Enable translation service', true),
    ('FEATURE_SENTIMENT_ANALYSIS', 'true', 'boolean', 'Enable sentiment analysis on feedback', true),
    ('FEATURE_EVENT_EXTRACTION', 'true', 'boolean', 'Enable automatic event extraction from documents', true),
    ('FEATURE_IMAGE_SEARCH', 'true', 'boolean', 'Enable image/multimedia search', true),
    ('FEATURE_SEMANTIC_ROUTER', 'true', 'boolean', 'Enable semantic routing to specialized models', true)
ON CONFLICT (config_key) DO NOTHING;

-- GIGW Compliance
INSERT INTO system_config (config_key, config_value, value_type, description, is_mutable) VALUES
    ('GIGW_LAST_UPDATED_DATE', 'CURRENT_TIMESTAMP', 'string', 'Last updated date for footer (ISO 8601)', true),
    ('MINISTRY_WEBSITE_CONTENT_MANAGED_BY', 'Ministry of Culture', 'string', 'Footer text: content managed by', false),
    ('WEBSITE_DESIGNED_DEVELOPED_BY', 'National Informatics Centre (NIC)', 'string', 'Footer text: design/development/hosting', false)
ON CONFLICT (config_key) DO NOTHING;

-- Application Environment
INSERT INTO system_config (config_key, config_value, value_type, description, is_mutable) VALUES
    ('APP_ENV', 'production', 'string', 'Application environment (development, staging, production)', false),
    ('APP_DEBUG', 'false', 'boolean', 'Enable debug mode', false),
    ('APP_LOG_LEVEL', 'INFO', 'string', 'Logging level (DEBUG, INFO, WARNING, ERROR)', true)
ON CONFLICT (config_key) DO NOTHING;
