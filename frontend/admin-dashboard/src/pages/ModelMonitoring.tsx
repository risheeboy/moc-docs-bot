import React, { useState, useEffect } from 'react';
import { ModelMonitoringData } from '../types/index';
import api from '../services/api';
import ChartWrapper from '../components/ChartWrapper';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import '../styles/ModelMonitoring.css';

const ModelMonitoring: React.FC = () => {
  const [data, setData] = useState<ModelMonitoringData | null>(null);
  const [period, setPeriod] = useState('7d');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchMetrics();
  }, [period]);

  const fetchMetrics = async () => {
    try {
      setLoading(true);
      setError(null);
      const metricsData = await api.getModelMetrics(period);
      setData(metricsData);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load model metrics';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="model-monitoring">
      <div className="monitoring-header">
        <h1>Model Monitoring (Langfuse)</h1>
        <div className="period-selector">
          <label>Period:</label>
          <select value={period} onChange={(e) => setPeriod(e.target.value)}>
            <option value="1d">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>
        </div>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      {data && (
        <>
          <div className="metrics-overview">
            {data.metrics.map((metric) => (
              <div key={metric.model_name} className="metric-card">
                <h4>{metric.model_name}</h4>
                <div className="metric-grid">
                  <div className="metric-item">
                    <span className="metric-label">Requests</span>
                    <span className="metric-value">{metric.total_requests}</span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">Avg Latency</span>
                    <span className="metric-value">{metric.avg_latency_ms.toFixed(0)}ms</span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">Tokens Generated</span>
                    <span className="metric-value">
                      {(metric.total_tokens_generated / 1000).toFixed(1)}K
                    </span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">Cost</span>
                    <span className="metric-value">${metric.total_cost_usd.toFixed(2)}</span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">Success Rate</span>
                    <span className={`metric-value ${metric.success_rate > 0.95 ? 'success' : 'warning'}`}>
                      {(metric.success_rate * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">Error Rate</span>
                    <span className={`metric-value ${metric.error_rate < 0.05 ? 'success' : 'danger'}`}>
                      {(metric.error_rate * 100).toFixed(2)}%
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="monitoring-charts">
            <ChartWrapper
              title="Request Volume by Model"
              subtitle="Number of requests processed"
              loading={loading}
            >
              <ResponsiveContainer width="100%" height={300}>
                <BarChart
                  data={data.metrics}
                  layout="vertical"
                  margin={{ top: 5, right: 30, left: 200, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="model_name" type="category" width={190} />
                  <Tooltip />
                  <Bar dataKey="total_requests" fill="#3b82f6" />
                </BarChart>
              </ResponsiveContainer>
            </ChartWrapper>

            <ChartWrapper
              title="Average Latency by Model"
              subtitle="Response time in milliseconds"
              loading={loading}
            >
              <ResponsiveContainer width="100%" height={300}>
                <BarChart
                  data={data.metrics}
                  layout="vertical"
                  margin={{ top: 5, right: 30, left: 200, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="model_name" type="category" width={190} />
                  <Tooltip formatter={(value) => `${value.toFixed(0)}ms`} />
                  <Bar dataKey="avg_latency_ms" fill="#f59e0b" />
                </BarChart>
              </ResponsiveContainer>
            </ChartWrapper>

            <ChartWrapper
              title="Cost Analysis by Model"
              subtitle="Total cost in USD"
              loading={loading}
            >
              <ResponsiveContainer width="100%" height={300}>
                <BarChart
                  data={data.metrics}
                  layout="vertical"
                  margin={{ top: 5, right: 30, left: 200, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="model_name" type="category" width={190} />
                  <Tooltip formatter={(value) => `$${value.toFixed(2)}`} />
                  <Bar dataKey="total_cost_usd" fill="#10b981" />
                </BarChart>
              </ResponsiveContainer>
            </ChartWrapper>

            <ChartWrapper
              title="Success Rate by Model"
              subtitle="Percentage of successful requests"
              loading={loading}
            >
              <ResponsiveContainer width="100%" height={300}>
                <BarChart
                  data={data.metrics.map((m) => ({
                    ...m,
                    success_rate_pct: m.success_rate * 100,
                  }))}
                  layout="vertical"
                  margin={{ top: 5, right: 30, left: 200, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" domain={[0, 100]} />
                  <YAxis dataKey="model_name" type="category" width={190} />
                  <Tooltip formatter={(value) => `${value.toFixed(1)}%`} />
                  <Bar dataKey="success_rate_pct" fill="#10b981" />
                </BarChart>
              </ResponsiveContainer>
            </ChartWrapper>
          </div>

          <div className="monitoring-info">
            <div className="info-card">
              <h3>About Model Monitoring</h3>
              <p>
                This dashboard pulls metrics from <strong>Langfuse</strong>, our LLM observability
                platform. It tracks:
              </p>
              <ul>
                <li>Request volume and throughput</li>
                <li>Response latency and performance</li>
                <li>Token usage and cost tracking</li>
                <li>Error rates and quality metrics</li>
                <li>Model-specific performance analysis</li>
              </ul>
            </div>

            <div className="info-card">
              <h3>Interpretation Guide</h3>
              <ul>
                <li>
                  <strong>Latency:</strong> Lower is better. Target &lt; 1000ms for real-time
                </li>
                <li>
                  <strong>Success Rate:</strong> Aim for &gt; 95% to ensure reliability
                </li>
                <li>
                  <strong>Cost:</strong> Monitor for cost optimization opportunities
                </li>
                <li>
                  <strong>Tokens:</strong> Track usage for budget planning
                </li>
              </ul>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default ModelMonitoring;
