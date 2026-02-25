import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import Dashboard from '../src/pages/Dashboard';
import api from '../src/services/api';

// Mock the api module
vi.mock('../src/services/api');

const mockMetrics = {
  query_volume_today: 1234,
  query_volume_change_percent: 15.5,
  avg_response_time_ms: 245.6,
  response_time_change_percent: -5.2,
  active_sessions: 56,
  sessions_change_percent: 8.3,
  user_satisfaction_score: 4.2,
  satisfaction_change_percent: 2.1,
  timestamp: new Date().toISOString(),
};

describe('Dashboard Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders dashboard title', async () => {
    (api.getDashboardMetrics as any).mockResolvedValueOnce(mockMetrics);

    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
    });
  });

  it('displays loading state initially', () => {
    (api.getDashboardMetrics as any).mockImplementationOnce(
      () => new Promise(() => {}) // Never resolves
    );

    render(<Dashboard />);

    expect(screen.getByText('Loading metrics...')).toBeInTheDocument();
  });

  it('displays metrics after loading', async () => {
    (api.getDashboardMetrics as any).mockResolvedValueOnce(mockMetrics);

    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getAllByText(/Query Volume/).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/Avg Response Time/).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/Active Sessions/).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/User Satisfaction/).length).toBeGreaterThan(0);
    });
  });

  it('displays error message on fetch failure', async () => {
    const errorMessage = 'Failed to fetch metrics';
    (api.getDashboardMetrics as any).mockRejectedValueOnce(new Error(errorMessage));

    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });
  });

  it('displays correct metric values', async () => {
    (api.getDashboardMetrics as any).mockResolvedValueOnce(mockMetrics);

    const { container } = render(<Dashboard />);

    await waitFor(() => {
      // Check for query volume
      expect(screen.getByText(/1,234/)).toBeInTheDocument(); // query_volume_today
      // Check for response time value - can be rounded or formatted (245.6 -> 246 or 245)
      const responseTimeText = container.textContent || '';
      expect(responseTimeText).toMatch(/\d+ms/);
      // Check for active sessions - appears multiple times so use getAllByText
      const sessionElements = screen.getAllByText(/56/);
      expect(sessionElements.length).toBeGreaterThan(0);
    });
  });

  it('displays status cards with health information', async () => {
    (api.getDashboardMetrics as any).mockResolvedValueOnce(mockMetrics);

    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/System Status/)).toBeInTheDocument();
      expect(screen.getByText(/API Gateway/)).toBeInTheDocument();
    });
  });

  it('calls getDashboardMetrics on mount', async () => {
    (api.getDashboardMetrics as any).mockResolvedValueOnce(mockMetrics);

    render(<Dashboard />);

    await waitFor(() => {
      expect(api.getDashboardMetrics).toHaveBeenCalledTimes(1);
    });
  });

  it('displays quick action buttons', async () => {
    (api.getDashboardMetrics as any).mockResolvedValueOnce(mockMetrics);

    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/Trigger Scrape Job/)).toBeInTheDocument();
      expect(screen.getByText(/Upload Document/)).toBeInTheDocument();
      expect(screen.getByText(/View Analytics/)).toBeInTheDocument();
    });
  });
});
