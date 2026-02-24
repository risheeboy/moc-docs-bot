-- Migration 012: Create model_versions table
-- Tracks fine-tuned model versions and their evaluation metrics

CREATE TABLE IF NOT EXISTS model_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id VARCHAR(100) NOT NULL,                 -- e.g., 'llama-3.1-8b-ministry-v1'
    version VARCHAR(50) NOT NULL,                   -- e.g., 'v1.0', 'v1.2-finetuned'
    base_model VARCHAR(255) NOT NULL,               -- e.g., 'meta-llama/Llama-3.1-8B-Instruct-AWQ'
    model_status VARCHAR(50) NOT NULL DEFAULT 'training', -- 'training', 'evaluating', 'approved', 'deprecated'
    minio_path VARCHAR(500),                        -- Path to model weights in MinIO
    eval_score FLOAT,                               -- Overall evaluation score (0.0-1.0)
    exact_match FLOAT,                              -- Metric: exact match percentage
    f1_score FLOAT,                                 -- Metric: F1 score
    bleu_score FLOAT,                               -- Metric: BLEU score
    ndcg_score FLOAT,                               -- Metric: normalized discounted cumulative gain
    hallucination_rate FLOAT,                       -- Metric: hallucination rate (0.0-1.0)
    llm_judge_score FLOAT,                          -- Metric: score from LLM judge (0.0-5.0)
    eval_samples INT,                               -- Number of samples used in evaluation
    eval_datetime TIMESTAMPTZ,                      -- When evaluation was completed
    training_duration_minutes INT,                  -- Training time
    approver_id UUID REFERENCES users(id) ON DELETE SET NULL,
    approval_notes TEXT,
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for efficient lookups
CREATE INDEX idx_model_versions_model_id ON model_versions(model_id);
CREATE INDEX idx_model_versions_version ON model_versions(version);
CREATE INDEX idx_model_versions_model_status ON model_versions(model_status);
CREATE INDEX idx_model_versions_created_at ON model_versions(created_at);
CREATE INDEX idx_model_versions_eval_score ON model_versions(eval_score);

-- Composite index for finding best approved model
CREATE INDEX idx_model_versions_approved_score ON model_versions(model_status, eval_score DESC) WHERE model_status = 'approved';

-- Add comments for clarity
COMMENT ON TABLE model_versions IS 'Fine-tuned language model versions with evaluation metrics and deployment status';
COMMENT ON COLUMN model_versions.model_status IS 'Deployment status: training → evaluating → approved (or deprecated)';
COMMENT ON COLUMN model_versions.eval_score IS 'Overall evaluation metric (0.0-1.0); used for model selection';
COMMENT ON COLUMN model_versions.hallucination_rate IS 'Percentage of outputs containing hallucinations (0.0-1.0)';
COMMENT ON COLUMN model_versions.llm_judge_score IS 'Score from LLM-as-judge evaluation (0.0-5.0 scale)';
