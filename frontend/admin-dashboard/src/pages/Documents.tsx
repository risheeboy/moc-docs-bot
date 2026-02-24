import React, { useState, useEffect } from 'react';
import { Document, DocumentListResponse } from '../types/index';
import api from '../services/api';
import DataTable, { Column } from '../components/DataTable';
import DocumentUploader from '../components/DocumentUploader';
import '../styles/Documents.css';

const Documents: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentListResponse | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showUploader, setShowUploader] = useState(false);

  useEffect(() => {
    fetchDocuments();
  }, [page]);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.listDocuments(page, 20);
      setDocuments(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load documents';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (doc: Document) => {
    if (!window.confirm(`Are you sure you want to delete "${doc.title}"?`)) return;

    try {
      await api.deleteDocument(doc.document_id);
      setDocuments(
        documents
          ? {
              ...documents,
              items: documents.items.filter((d) => d.document_id !== doc.document_id),
            }
          : null
      );
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete document';
      setError(errorMessage);
    }
  };

  const handleUploadSuccess = () => {
    setShowUploader(false);
    setPage(1);
    fetchDocuments();
  };

  const columns: Column<Document>[] = [
    {
      key: 'title',
      header: 'Title',
      width: '30%',
    },
    {
      key: 'source_site',
      header: 'Source Site',
      width: '20%',
    },
    {
      key: 'status',
      header: 'Status',
      width: '15%',
      render: (value) => {
        const status = String(value);
        const badgeClass =
          status === 'completed'
            ? 'badge-success'
            : status === 'failed'
              ? 'badge-danger'
              : 'badge-warning';
        return <span className={`badge ${badgeClass}`}>{status}</span>;
      },
    },
    {
      key: 'chunk_count',
      header: 'Chunks',
      width: '10%',
    },
    {
      key: 'uploaded_at',
      header: 'Uploaded',
      width: '15%',
      render: (value) => new Date(String(value)).toLocaleDateString(),
    },
  ];

  return (
    <div className="documents">
      <div className="documents-header">
        <h1>Document Management</h1>
        <button className="btn btn-primary" onClick={() => setShowUploader(!showUploader)}>
          {showUploader ? 'Cancel' : 'Upload Document'}
        </button>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      {showUploader && (
        <div className="uploader-section">
          <DocumentUploader
            onUploadSuccess={handleUploadSuccess}
            onUploadError={(err) => setError(err)}
          />
        </div>
      )}

      {documents && (
        <DataTable<Document>
          columns={columns}
          data={documents.items}
          loading={loading}
          error={error || undefined}
          actions={[
            {
              label: 'Delete',
              onClick: handleDelete,
              variant: 'danger',
            },
          ]}
          pagination={{
            total: documents.total,
            page: documents.page,
            page_size: documents.page_size,
            total_pages: documents.total_pages,
            onPageChange: setPage,
          }}
        />
      )}
    </div>
  );
};

export default Documents;
