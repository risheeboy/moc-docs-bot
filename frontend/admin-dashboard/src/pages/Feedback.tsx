import React, { useState, useEffect } from 'react';
import { Feedback, FeedbackListResponse, FeedbackSentimentSummary } from '../types/index';
import api from '../services/api';
import DataTable, { Column } from '../components/DataTable';
import ChartWrapper from '../components/ChartWrapper';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import '../styles/Feedback.css';

const COLORS = ['#10b981', '#ef4444', '#f59e0b'];

const Feedback: React.FC = () => {
  const [feedback, setFeedback] = useState<FeedbackListResponse | null>(null);
  const [sentiment, setSentiment] = useState<FeedbackSentimentSummary | null>(null);
  const [page, setPage] = useState(1);
  const [period, setPeriod] = useState('30d');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchFeedback();
  }, [page]);

  useEffect(() => {
    fetchSentimentSummary();
  }, [period]);

  const fetchFeedback = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.listFeedback(page, 20);
      setFeedback(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load feedback';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const fetchSentimentSummary = async () => {
    try {
      const data = await api.getFeedbackSentimentSummary(period);
      setSentiment(data);
    } catch (err) {
      console.error('Failed to load sentiment summary:', err);
    }
  };

  const columns: Column<Feedback>[] = [
    {
      key: 'feedback_id',
      header: 'ID',
      width: '12%',
      render: (value) => String(value).slice(0, 8),
    },
    {
      key: 'rating',
      header: 'Rating',
      width: '10%',
      render: (value) => {
        const rating = Number(value);
        const stars = '⭐'.repeat(rating);
        return `${stars} ${rating}/5`;
      },
    },
    {
      key: 'sentiment',
      header: 'Sentiment',
      width: '15%',
      render: (value) => {
        const sentiment = String(value);
        const badgeClass =
          sentiment === 'positive'
            ? 'badge-success'
            : sentiment === 'negative'
              ? 'badge-danger'
              : 'badge-warning';
        return <span className={`badge ${badgeClass}`}>{sentiment}</span>;
      },
    },
    {
      key: 'comment',
      header: 'Comment',
      width: '35%',
      render: (value) => (value ? String(value).substring(0, 50) + '...' : '-'),
    },
    {
      key: 'created_at',
      header: 'Date',
      width: '15%',
      render: (value) => new Date(String(value)).toLocaleDateString(),
    },
  ];

  const sentimentData = sentiment
    ? [
        { name: 'Positive', value: sentiment.positive_count },
        { name: 'Negative', value: sentiment.negative_count },
        { name: 'Neutral', value: sentiment.neutral_count },
      ]
    : [];

  const ratingData = [
    { rating: '1 Star', count: 0 },
    { rating: '2 Stars', count: 0 },
    { rating: '3 Stars', count: 0 },
    { rating: '4 Stars', count: 0 },
    { rating: '5 Stars', count: 0 },
  ];

  // Calculate distribution from feedback data
  if (feedback) {
    feedback.items.forEach((item) => {
      const idx = Math.min(Math.max(item.rating - 1, 0), 4);
      ratingData[idx].count += 1;
    });
  }

  return (
    <div className="feedback">
      <div className="feedback-header">
        <h1>Feedback & Sentiment Analysis</h1>
        <div className="period-selector">
          <label>Period:</label>
          <select value={period} onChange={(e) => setPeriod(e.target.value)}>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 90 Days</option>
          </select>
        </div>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      {sentiment && (
        <div className="sentiment-stats">
          <div className="stat-card">
            <h4>Total Feedback</h4>
            <p className="stat-value">{sentiment.total_feedback}</p>
          </div>
          <div className="stat-card positive">
            <h4>Positive</h4>
            <p className="stat-value">{sentiment.positive_count}</p>
            <p className="stat-percent">
              {((sentiment.positive_count / sentiment.total_feedback) * 100).toFixed(1)}%
            </p>
          </div>
          <div className="stat-card negative">
            <h4>Negative</h4>
            <p className="stat-value">{sentiment.negative_count}</p>
            <p className="stat-percent">
              {((sentiment.negative_count / sentiment.total_feedback) * 100).toFixed(1)}%
            </p>
          </div>
          <div className="stat-card neutral">
            <h4>Neutral</h4>
            <p className="stat-value">{sentiment.neutral_count}</p>
            <p className="stat-percent">
              {((sentiment.neutral_count / sentiment.total_feedback) * 100).toFixed(1)}%
            </p>
          </div>
          <div className="stat-card">
            <h4>Avg Rating</h4>
            <p className="stat-value">{sentiment.avg_rating.toFixed(2)}</p>
            <p className="stat-unit">/5.0</p>
          </div>
        </div>
      )}

      <div className="feedback-charts">
        <ChartWrapper
          title="Sentiment Distribution"
          subtitle={`Based on ${sentiment?.total_feedback || 0} feedback entries`}
          loading={!sentiment}
        >
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={sentimentData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={80}
                label
              >
                {sentimentData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </ChartWrapper>

        <ChartWrapper
          title="Rating Distribution"
          subtitle="Breakdown by star rating"
          loading={!feedback}
        >
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={ratingData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="rating" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </ChartWrapper>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Recent Feedback</h3>
        </div>
        <div className="card-body">
          {feedback && (
            <DataTable<Feedback>
              columns={columns}
              data={feedback.items}
              loading={loading}
              error={error || undefined}
              pagination={{
                total: feedback.total,
                page: feedback.page,
                page_size: feedback.page_size,
                total_pages: feedback.total_pages,
                onPageChange: setPage,
              }}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default Feedback;
