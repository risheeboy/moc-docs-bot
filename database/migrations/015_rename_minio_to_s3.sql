-- 015_rename_minio_to_s3.sql
-- Rename legacy MinIO column names to S3
BEGIN;

ALTER TABLE documents RENAME COLUMN minio_path TO s3_path;
ALTER TABLE model_versions RENAME COLUMN minio_path TO s3_path;

-- Update comments
COMMENT ON COLUMN documents.s3_path IS 'Path in AWS S3 object storage';
COMMENT ON COLUMN model_versions.s3_path IS 'Path to model weights in AWS S3';

COMMIT;
