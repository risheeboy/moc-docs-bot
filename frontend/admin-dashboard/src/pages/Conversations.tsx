import React, { useState, useEffect } from 'react';
import { Conversation, ConversationDetail, ConversationListResponse } from '../types/index';
import api from '../services/api';
import DataTable, { Column } from '../components/DataTable';
import '../styles/Conversations.css';

const Conversations: React.FC = () => {
  const [conversations, setConversations] = useState<ConversationListResponse | null>(null);
  const [selectedConversation, setSelectedConversation] = useState<ConversationDetail | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchConversations();
  }, [page]);

  const fetchConversations = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.listConversations(page, 20);
      setConversations(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load conversations';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetails = async (conversation: Conversation) => {
    try {
      setDetailLoading(true);
      const detail = await api.getConversationDetail(conversation.session_id);
      setSelectedConversation(detail);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load conversation';
      setError(errorMessage);
    } finally {
      setDetailLoading(false);
    }
  };

  const columns: Column<Conversation>[] = [
    {
      key: 'session_id',
      header: 'Session ID',
      width: '20%',
      render: (value) => String(value).slice(0, 8),
    },
    {
      key: 'language',
      header: 'Language',
      width: '12%',
    },
    {
      key: 'query_count',
      header: 'Queries',
      width: '10%',
    },
    {
      key: 'created_at',
      header: 'Started',
      width: '18%',
      render: (value) => new Date(String(value)).toLocaleString(),
    },
    {
      key: 'last_interaction_at',
      header: 'Last Activity',
      width: '18%',
      render: (value) => {
        const date = new Date(String(value));
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);
        if (diffMins < 1) return 'just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        const diffHours = Math.floor(diffMins / 60);
        if (diffHours < 24) return `${diffHours}h ago`;
        return date.toLocaleDateString();
      },
    },
    {
      key: 'satisfaction_score',
      header: 'Rating',
      width: '12%',
      render: (value) => {
        if (!value) return '-';
        return `${Number(value)}/5`;
      },
    },
  ];

  return (
    <div className="conversations">
      <div className="conversations-header">
        <h1>Conversations</h1>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      <div className="conversations-container">
        <div className="conversations-list">
          {conversations && (
            <DataTable<Conversation>
              columns={columns}
              data={conversations.items}
              loading={loading}
              error={error || undefined}
              onRowClick={handleViewDetails}
              pagination={{
                total: conversations.total,
                page: conversations.page,
                page_size: conversations.page_size,
                total_pages: conversations.total_pages,
                onPageChange: setPage,
              }}
            />
          )}
        </div>

        {selectedConversation && (
          <div className="conversation-detail">
            <div className="detail-header">
              <h3>Conversation Details</h3>
              <button
                className="btn btn-outline btn-sm"
                onClick={() => setSelectedConversation(null)}
              >
                Close
              </button>
            </div>

            {detailLoading && (
              <div className="detail-loading">
                <div className="spinner"></div>
                <p>Loading conversation...</p>
              </div>
            )}

            {!detailLoading && selectedConversation && (
              <div className="detail-content">
                <div className="detail-info">
                  <div className="info-item">
                    <span className="info-label">Session ID:</span>
                    <span className="info-value">{selectedConversation.session_id}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Language:</span>
                    <span className="info-value">{selectedConversation.language}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Queries:</span>
                    <span className="info-value">{selectedConversation.query_count}</span>
                  </div>
                  {selectedConversation.satisfaction_score && (
                    <div className="info-item">
                      <span className="info-label">Rating:</span>
                      <span className="info-value">
                        {selectedConversation.satisfaction_score}/5 ⭐
                      </span>
                    </div>
                  )}
                </div>

                <div className="turns-section">
                  <h4>Conversation Transcript</h4>
                  <div className="turns-list">
                    {selectedConversation.turns.map((turn) => (
                      <div key={turn.turn_id} className={`turn ${turn.role}`}>
                        <div className="turn-header">
                          <strong>{turn.role === 'user' ? 'User' : 'Assistant'}</strong>
                          <span className="turn-time">
                            {new Date(turn.timestamp).toLocaleTimeString()}
                          </span>
                        </div>
                        <div className="turn-content">{turn.content}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Conversations;
