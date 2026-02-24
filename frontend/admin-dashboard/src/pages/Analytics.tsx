import React, { useState } from 'react';
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
} from 'recharts';
import { useAnalytics } from '../hooks/useAnalytics';
import ChartWrapper from '../components/ChartWrapper';
import '../styles/Analytics.css';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

const Analytics: React.FC = () => {
  const [period, setPeriod] = useState('7d');
  const { data, isLoading, error } = useAnalytics(period);

  const handlePeriodChange = (newPeriod: string) => {
    setPeriod(newPeriod);
  };

  return (
    <div className="analytics">
      <div className="analytics-header">
        <h1>Analytics</h1>
        <div className="period-selector">
          <label>Period:</label>
          <select value={period} onChange={(e) => handlePeriodChange(e.target.value)}>
            <option value="1d">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 90 Days</option>
          </select>
        </div>
      </div>

      {data && (
        <>
          {/* Language Distribution */}
          <ChartWrapper
            title="Language Distribution"
            subtitle="Query distribution by language"
            loading={isLoading}
            error={error}
          >
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={data.language_distribution}
                  dataKey="query_count"
                  nameKey="language"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  label
                >
                  {data.language_distribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </ChartWrapper>

          {/* Topic Distribution */}
          <ChartWrapper
            title="Topic Distribution"
            subtitle="Query distribution by topic"
            loading={isLoading}
            error={error}
          >
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={data.topic_distribution}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="topic" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="query_count" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </ChartWrapper>

          {/* Model Usage */}
          <ChartWrapper
            title="Model Usage Metrics"
            subtitle="Performance and cost by model"
            loading={isLoading}
            error={error}
          >
            <div className="model-metrics-table">
              <table>
                <thead>
                  <tr>
                    <th>Model</th>
                    <th>Usage Count</th>
                    <th>Avg Latency</th>
                    <th>Cost (USD)</th>
                  </tr>
                </thead>
                <tbody>
                  {data.model_usage.map((metric) => (
                    <tr key={metric.model_name}>
                      <td className="model-name">{metric.model_name}</td>
                      <td>{metric.usage_count.toLocaleString()}</td>
                      <td>{metric.avg_latency_ms.toFixed(0)}ms</td>
                      <td className="cost">${metric.cost_usd.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </ChartWrapper>

          {/* Satisfaction Trends */}
          <ChartWrapper
            title="User Satisfaction Trends"
            subtitle="Average satisfaction score over time"
            loading={isLoading}
            error={error}
          >
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={data.satisfaction_trends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis domain={[0, 5]} />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="avg_score"
                  stroke="#3b82f6"
                  name="Avg Score"
                />
              </LineChart>
            </ResponsiveContainer>
          </ChartWrapper>
        </>
      )}
    </div>
  );
};

export default Analytics;
