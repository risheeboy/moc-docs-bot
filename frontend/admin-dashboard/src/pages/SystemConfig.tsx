import React, { useState, useEffect } from 'react';
import { SystemConfig } from '../types/index';
import api from '../services/api';
import '../styles/SystemConfig.css';

const SystemConfiguration: React.FC = () => {
  const [config, setConfig] = useState<SystemConfig | null>(null);
  const [formData, setFormData] = useState<Partial<SystemConfig>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getSystemConfig();
      setConfig(data);
      setFormData(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load config';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, type, value } = e.target as any;
    const inputElement = e.target as HTMLInputElement;

    let newValue: unknown;
    if (type === 'checkbox') {
      newValue = inputElement.checked;
    } else if (type === 'number') {
      newValue = parseFloat(value);
    } else {
      newValue = value;
    }

    setFormData((prev) => ({
      ...prev,
      [name]: newValue,
    }));
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    try {
      setSaving(true);
      setError(null);
      setSuccess(null);
      await api.updateSystemConfig({ config: formData });
      setSuccess('Configuration updated successfully');
      fetchConfig();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save config';
      setError(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    if (config) {
      setFormData(config);
    }
  };

  if (loading) {
    return (
      <div className="system-config">
        <h1>System Configuration</h1>
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading configuration...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="system-config">
      <div className="config-header">
        <h1>System Configuration</h1>
        <p>Manage RAG and LLM system parameters</p>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      <form onSubmit={handleSubmit} className="config-form card">
        <div className="form-sections">
          <div className="form-section">
            <h3>RAG Configuration</h3>

            <div className="form-group">
              <label htmlFor="rag_confidence_threshold">
                Confidence Threshold (0-1)
              </label>
              <input
                type="number"
                id="rag_confidence_threshold"
                name="rag_confidence_threshold"
                min="0"
                max="1"
                step="0.01"
                value={formData.rag_confidence_threshold || 0}
                onChange={handleChange}
              />
              <small>Minimum confidence score for RAG responses (below threshold uses fallback)</small>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="rag_top_k">Top K Results</label>
                <input
                  type="number"
                  id="rag_top_k"
                  name="rag_top_k"
                  min="1"
                  max="50"
                  value={formData.rag_top_k || 10}
                  onChange={handleChange}
                />
              </div>

              <div className="form-group">
                <label htmlFor="rag_rerank_top_k">Rerank Top K</label>
                <input
                  type="number"
                  id="rag_rerank_top_k"
                  name="rag_rerank_top_k"
                  min="1"
                  max="20"
                  value={formData.rag_rerank_top_k || 5}
                  onChange={handleChange}
                />
              </div>

              <div className="form-group">
                <label htmlFor="rag_cache_ttl_seconds">Cache TTL (seconds)</label>
                <input
                  type="number"
                  id="rag_cache_ttl_seconds"
                  name="rag_cache_ttl_seconds"
                  min="60"
                  value={formData.rag_cache_ttl_seconds || 3600}
                  onChange={handleChange}
                />
              </div>
            </div>
          </div>

          <div className="form-section">
            <h3>Session Configuration</h3>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="session_idle_timeout_seconds">
                  Idle Timeout (seconds)
                </label>
                <input
                  type="number"
                  id="session_idle_timeout_seconds"
                  name="session_idle_timeout_seconds"
                  min="60"
                  value={formData.session_idle_timeout_seconds || 1800}
                  onChange={handleChange}
                />
              </div>

              <div className="form-group">
                <label htmlFor="session_max_turns">Max Turns</label>
                <input
                  type="number"
                  id="session_max_turns"
                  name="session_max_turns"
                  min="1"
                  max="100"
                  value={formData.session_max_turns || 50}
                  onChange={handleChange}
                />
              </div>
            </div>
          </div>

          <div className="form-section">
            <h3>LLM Configuration</h3>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="llm_temperature">Temperature (0-2)</label>
                <input
                  type="number"
                  id="llm_temperature"
                  name="llm_temperature"
                  min="0"
                  max="2"
                  step="0.1"
                  value={formData.llm_temperature || 0.7}
                  onChange={handleChange}
                />
                <small>Lower values = more deterministic, higher = more creative</small>
              </div>

              <div className="form-group">
                <label htmlFor="llm_max_tokens">Max Tokens</label>
                <input
                  type="number"
                  id="llm_max_tokens"
                  name="llm_max_tokens"
                  min="100"
                  max="4096"
                  value={formData.llm_max_tokens || 1024}
                  onChange={handleChange}
                />
              </div>
            </div>
          </div>

          <div className="form-section">
            <h3>Feature Flags</h3>

            <div className="checkbox-group">
              <label>
                <input
                  type="checkbox"
                  name="enable_voice_input"
                  checked={formData.enable_voice_input || false}
                  onChange={handleChange}
                />
                <span>Enable Voice Input</span>
              </label>
              <small>Allow users to input queries via voice</small>
            </div>

            <div className="checkbox-group">
              <label>
                <input
                  type="checkbox"
                  name="enable_translation"
                  checked={formData.enable_translation || false}
                  onChange={handleChange}
                />
                <span>Enable Translation</span>
              </label>
              <small>Enable multi-language translation support</small>
            </div>

            <div className="checkbox-group">
              <label>
                <input
                  type="checkbox"
                  name="enable_ocr"
                  checked={formData.enable_ocr || false}
                  onChange={handleChange}
                />
                <span>Enable OCR</span>
              </label>
              <small>Enable optical character recognition for document scanning</small>
            </div>

            <div className="checkbox-group">
              <label>
                <input
                  type="checkbox"
                  name="enable_sentiment_analysis"
                  checked={formData.enable_sentiment_analysis || false}
                  onChange={handleChange}
                />
                <span>Enable Sentiment Analysis</span>
              </label>
              <small>Analyze user feedback and conversation sentiment</small>
            </div>
          </div>
        </div>

        <div className="form-actions">
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? 'Saving...' : 'Save Configuration'}
          </button>
          <button
            type="button"
            className="btn btn-outline"
            onClick={handleReset}
            disabled={saving}
          >
            Reset
          </button>
        </div>
      </form>
    </div>
  );
};

export default SystemConfiguration;
