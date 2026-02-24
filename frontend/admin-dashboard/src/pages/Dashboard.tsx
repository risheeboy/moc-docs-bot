import React, { useState, useEffect } from 'react';
import { DashboardMetrics } from '../types/index';
import api from '../services/api';
import StatsCard from '../components/StatsCard';
import '../styles/Dashboard.css';

const Dashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>('');

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await api.getDashboardMetrics();
        setMetrics(data);
        setLastUpdated(new Date(data.timestamp).toLocaleTimeString());
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to load metrics';
        setError(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="dashboard">
        <h1>Dashboard</h1>
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading metrics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard">
        <h1>Dashboard</h1>
        <div className="alert alert-danger">{error}</div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Dashboard</h1>
        <p className="last-updated">Last updated: {lastUpdated}</p>
      </div>

      {metrics && (
        <>
          <div className="stats-grid">
            <StatsCard
              title="Query Volume"
              value={metrics.query_volume_today.toLocaleString()}
              change={metrics.query_volume_change_percent}
              changeLabel="from yesterday"
              icon="📊"
              color="primary"
            />
            <StatsCard
              title="Avg Response Time"
              value={`${metrics.avg_response_time_ms.toFixed(0)}ms`}
              change={-metrics.response_time_change_percent}
              changeLabel="from yesterday"
              icon="⚡"
              color="success"
            />
            <StatsCard
              title="Active Sessions"
              value={metrics.active_sessions.toLocaleString()}
              change={metrics.sessions_change_percent}
              changeLabel="from yesterday"
              icon="👥"
              color="info"
            />
            <StatsCard
              title="User Satisfaction"
              value={`${metrics.user_satisfaction_score.toFixed(1)}/5`}
              change={metrics.satisfaction_change_percent}
              changeLabel="from yesterday"
              icon="⭐"
              color="warning"
            />
          </div>

          <div className="dashboard-widgets">
            <div className="widget card">
              <div className="card-header">
                <h3>System Status</h3>
              </div>
              <div className="card-body">
                <div className="status-item">
                  <span className="status-label">API Gateway</span>
                  <span className="badge badge-success">Healthy</span>
                </div>
                <div className="status-item">
                  <span className="status-label">RAG Service</span>
                  <span className="badge badge-success">Healthy</span>
                </div>
                <div className="status-item">
                  <span className="status-label">LLM Service</span>
                  <span className="badge badge-success">Healthy</span>
                </div>
                <div className="status-item">
                  <span className="status-label">Vector Database</span>
                  <span className="badge badge-success">Healthy</span>
                </div>
              </div>
            </div>

            <div className="widget card">
              <div className="card-header">
                <h3>Quick Actions</h3>
              </div>
              <div className="card-body">
                <button className="btn btn-primary btn-block">
                  Trigger Scrape Job
                </button>
                <button className="btn btn-outline btn-block">
                  Upload Document
                </button>
                <button className="btn btn-outline btn-block">
                  View Analytics
                </button>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <h3>Key Metrics Overview</h3>
            </div>
            <div className="card-body">
              <div className="metrics-grid">
                <div className="metric-item">
                  <span className="metric-label">Queries Today</span>
                  <span className="metric-value">{metrics.query_volume_today}</span>
                </div>
                <div className="metric-item">
                  <span className="metric-label">Avg Response Time</span>
                  <span className="metric-value">{metrics.avg_response_time_ms.toFixed(0)}ms</span>
                </div>
                <div className="metric-item">
                  <span className="metric-label">Active Sessions</span>
                  <span className="metric-value">{metrics.active_sessions}</span>
                </div>
                <div className="metric-item">
                  <span className="metric-label">Satisfaction Score</span>
                  <span className="metric-value">
                    {metrics.user_satisfaction_score.toFixed(2)}/5
                  </span>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default Dashboard;
