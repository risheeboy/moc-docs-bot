import React, { useState } from 'react';
import '../styles/DataTable.css';

export interface Column<T> {
  key: keyof T;
  header: string;
  render?: (value: unknown, row: T) => React.ReactNode;
  width?: string;
}

export interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  loading?: boolean;
  error?: string;
  onRowClick?: (row: T) => void;
  actions?: Array<{
    label: string;
    onClick: (row: T) => void;
    variant?: 'primary' | 'danger' | 'warning';
  }>;
  pagination?: {
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
    onPageChange: (page: number) => void;
  };
}

const DataTable = <T extends { [key: string]: unknown }>({
  columns,
  data,
  loading = false,
  error,
  onRowClick,
  actions,
  pagination,
}: DataTableProps<T>) => {
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());

  const toggleRow = (index: number) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedRows(newExpanded);
  };

  if (loading) {
    return (
      <div className="data-table-loading">
        <div className="spinner"></div>
        <p>Loading data...</p>
      </div>
    );
  }

  if (error) {
    return <div className="alert alert-danger">Error: {error}</div>;
  }

  if (data.length === 0) {
    return <div className="alert alert-info">No data available</div>;
  }

  return (
    <div className="data-table-wrapper">
      <div className="table-responsive">
        <table className="data-table">
          <thead>
            <tr>
              {actions && <th style={{ width: '40px' }}></th>}
              {columns.map((col) => (
                <th key={String(col.key)} style={{ width: col.width }}>
                  {col.header}
                </th>
              ))}
              {actions && actions.length > 0 && <th style={{ width: '150px' }}>Actions</th>}
            </tr>
          </thead>
          <tbody>
            {data.map((row, rowIndex) => (
              <React.Fragment key={rowIndex}>
                <tr
                  className={onRowClick ? 'clickable' : ''}
                  onClick={() => onRowClick?.(row)}
                >
                  {actions && (
                    <td>
                      <button
                        className="btn-expand"
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleRow(rowIndex);
                        }}
                      >
                        {expandedRows.has(rowIndex) ? '▼' : '▶'}
                      </button>
                    </td>
                  )}
                  {columns.map((col) => (
                    <td key={String(col.key)}>
                      {col.render
                        ? col.render(row[col.key], row)
                        : String(row[col.key] ?? '')}
                    </td>
                  ))}
                  {actions && actions.length > 0 && (
                    <td>
                      {expandedRows.has(rowIndex) && (
                        <div className="row-actions">
                          {actions.map((action, idx) => (
                            <button
                              key={idx}
                              className={`btn btn-sm btn-${action.variant || 'primary'}`}
                              onClick={(e) => {
                                e.stopPropagation();
                                action.onClick(row);
                              }}
                            >
                              {action.label}
                            </button>
                          ))}
                        </div>
                      )}
                    </td>
                  )}
                </tr>
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>

      {pagination && (
        <div className="table-pagination">
          <div className="pagination-info">
            Showing {(pagination.page - 1) * pagination.page_size + 1} to{' '}
            {Math.min(pagination.page * pagination.page_size, pagination.total)} of{' '}
            {pagination.total} results
          </div>
          <div className="pagination-controls">
            <button
              className="btn btn-outline btn-sm"
              disabled={pagination.page === 1}
              onClick={() => pagination.onPageChange(pagination.page - 1)}
            >
              Previous
            </button>
            <span className="pagination-current">
              Page {pagination.page} of {pagination.total_pages}
            </span>
            <button
              className="btn btn-outline btn-sm"
              disabled={pagination.page >= pagination.total_pages}
              onClick={() => pagination.onPageChange(pagination.page + 1)}
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default DataTable;
