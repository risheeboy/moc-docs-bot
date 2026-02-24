import React, { useState, useEffect } from 'react';
import { AuditLogEntry, AuditLogListResponse } from '../types/index';
import api from '../services/api';
import DataTable, { Column } from '../components/DataTable';
import '../styles/AuditLog.css';

const AuditLog: React.FC = () => {
  const [logs, setLogs] = useState<AuditLogListResponse | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState({
    action: '',
    resource_type: '',
    user_id: '',
  });

  useEffect(() => {
    fetchLogs();
  }, [page, filters]);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      setError(null);
      const activeFilters = Object.fromEntries(
        Object.entries(filters).filter(([, v]) => v !== '')
      );
      const data = await api.listAuditLog(page, 50, activeFilters);
      setLogs(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load audit log';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFilters((prev) => ({
      ...prev,
      [name]: value,
    }));
    setPage(1);
  };

  const columns: Column<AuditLogEntry>[] = [
    {
      key: 'timestamp',
      header: 'Time',
      width: '18%',
      render: (value) => new Date(String(value)).toLocaleString(),
    },
    {
      key: 'username',
      header: 'User',
      width: '12%',
    },
    {
      key: 'action',
      header: 'Action',
      width: '15%',
    },
    {
      key: 'resource_type',
      header: 'Resource Type',
      width: '15%',
    },
    {
      key: 'status',
      header: 'Status',
      width: '10%',
      render: (value) => {
        const status = String(value);
        const badgeClass = status === 'success' ? 'badge-success' : 'badge-danger';
        return <span className={`badge ${badgeClass}`}>{status}</span>;
      },
    },
    {
      key: 'ip_address',
      header: 'IP Address',
      width: '15%',
    },
  ];

  return (
    <div className="audit-log">
      <div className="audit-header">
        <h1>Audit Log</h1>
        <p>Track all system activities and changes</p>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      <div className="filters-section card">
        <div className="filters-header">
          <h3>Filters</h3>
        </div>
        <div className="filters-grid">
          <div className="filter-group">
            <label htmlFor="action">Action</label>
            <input
              type="text"
              id="action"
              name="action"
              placeholder="e.g., CREATE, UPDATE, DELETE"
              value={filters.action}
              onChange={handleFilterChange}
            />
          </div>

          <div className="filter-group">
            <label htmlFor="resource_type">Resource Type</label>
            <input
              type="text"
              id="resource_type"
              name="resource_type"
              placeholder="e.g., DOCUMENT, CONFIG, USER"
              value={filters.resource_type}
              onChange={handleFilterChange}
            />
          </div>

          <div className="filter-group">
            <label htmlFor="user_id">User ID</label>
            <input
              type="text"
              id="user_id"
              name="user_id"
              placeholder="Filter by user"
              value={filters.user_id}
              onChange={handleFilterChange}
            />
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Activity Log</h3>
        </div>
        <div className="card-body">
          {logs && (
            <DataTable<AuditLogEntry>
              columns={columns}
              data={logs.items}
              loading={loading}
              error={error || undefined}
              pagination={{
                total: logs.total,
                page: logs.page,
                page_size: logs.page_size,
                total_pages: logs.total_pages,
                onPageChange: setPage,
              }}
            />
          )}
        </div>
      </div>

      <div className="info-section">
        <div className="info-card">
          <h4>Audit Log Features</h4>
          <ul>
            <li>Complete tracking of all administrative actions</li>
            <li>Searchable by user, action, resource type, and date</li>
            <li>Records success/failure status for each action</li>
            <li>IP address logging for security tracking</li>
            <li>Detailed metadata for each change</li>
            <li>Retention: 2 years of historical data</li>
          </ul>
        </div>

        <div className="info-card">
          <h4>Common Actions</h4>
          <ul>
            <li>CREATE - New resource created</li>
            <li>UPDATE - Resource configuration changed</li>
            <li>DELETE - Resource removed</li>
            <li>UPLOAD - Document or file uploaded</li>
            <li>TRIGGER - Job or scrape initiated</li>
            <li>LOGIN - User authentication</li>
            <li>CONFIG_CHANGE - System configuration updated</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default AuditLog;
