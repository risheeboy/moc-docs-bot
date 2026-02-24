import React, { useState, useEffect } from 'react';
import { ScrapeJob } from '../types/index';
import api from '../services/api';
import DataTable, { Column } from '../components/DataTable';
import '../styles/ScrapeJobs.css';

const MINISTRY_SITES = [
  'culture.gov.in',
  'asi.nic.in',
  'indianmuseums.org',
  'indology.gov.in',
  'nmaind.gov.in',
  'National_Museum_Delhi.gov.in',
  'nationalmuseumdelhimp.gov.in',
  'sanchi.nic.in',
  'khanebolanonline.gov.in',
  'ccrtindia.gov.in',
  'heritage.gov.in',
  'archindiagovernment.gov.in',
  'craft.gov.in',
  'handlooms.gov.in',
  'handicraftsexport.gov.in',
  'handicraft.ac.in',
  'craftscouncil.gov.in',
  'weavers.gov.in',
  'craftmarkfoundation.gov.in',
  'craftmark.gov.in',
  'nift.ac.in',
  'nsd.ac.in',
  'rabindrasadandelhi.gov.in',
  'nizammuddin.org',
  'aripan.org',
  'artandindia.org',
  'culturalheritage.gov.in',
  'tourism.gov.in',
  'archaeology.gov.in',
  'heritage-conservation.gov.in',
];

const ScrapeJobs: React.FC = () => {
  const [jobs, setJobs] = useState<ScrapeJob[]>([]);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [triggering, setTriggering] = useState(false);
  const [selectedSites, setSelectedSites] = useState<Set<string>>(new Set());

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [page]);

  const fetchJobs = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.listScrapeJobs(page, 20);
      setJobs(data.items);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load scrape jobs';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleTriggerJob = async () => {
    if (selectedSites.size === 0) {
      setError('Please select at least one site');
      return;
    }

    try {
      setTriggering(true);
      setError(null);
      const targetUrls = Array.from(selectedSites).map((site) => `https://${site}`);
      await api.triggerScrapeJob({
        target_urls: targetUrls,
        spider_type: 'auto',
        force_rescrape: false,
      });
      setSelectedSites(new Set());
      fetchJobs();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to trigger scrape job';
      setError(errorMessage);
    } finally {
      setTriggering(false);
    }
  };

  const handleSiteToggle = (site: string) => {
    const newSelected = new Set(selectedSites);
    if (newSelected.has(site)) {
      newSelected.delete(site);
    } else {
      newSelected.add(site);
    }
    setSelectedSites(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedSites.size === MINISTRY_SITES.length) {
      setSelectedSites(new Set());
    } else {
      setSelectedSites(new Set(MINISTRY_SITES));
    }
  };

  const columns: Column<ScrapeJob>[] = [
    {
      key: 'job_id',
      header: 'Job ID',
      width: '20%',
      render: (value) => String(value).slice(0, 8),
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
      key: 'progress',
      header: 'Progress',
      width: '25%',
      render: (value) => {
        const prog = value as { pages_crawled: number; pages_total: number };
        const pct =
          prog.pages_total > 0 ? ((prog.pages_crawled / prog.pages_total) * 100).toFixed(0) : 0;
        return (
          <div className="progress-cell">
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${pct}%` }}></div>
            </div>
            <span className="progress-text">
              {prog.pages_crawled}/{prog.pages_total}
            </span>
          </div>
        );
      },
    },
    {
      key: 'elapsed_seconds',
      header: 'Elapsed',
      width: '15%',
      render: (value) => `${Math.round(Number(value))}s`,
    },
  ];

  return (
    <div className="scrape-jobs">
      <div className="scrape-jobs-header">
        <h1>Scrape Jobs</h1>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      <div className="card scrape-trigger">
        <div className="card-header">
          <h3>Trigger New Scrape Job</h3>
          <p className="card-subtitle">Select Ministry websites to scrape</p>
        </div>
        <div className="card-body">
          <div className="sites-selector">
            <div className="selector-controls">
              <button className="btn btn-outline btn-sm" onClick={handleSelectAll}>
                {selectedSites.size === MINISTRY_SITES.length ? 'Deselect All' : 'Select All'}
              </button>
              <span className="selection-count">
                {selectedSites.size} of {MINISTRY_SITES.length} selected
              </span>
            </div>

            <div className="sites-grid">
              {MINISTRY_SITES.map((site) => (
                <label key={site} className="site-checkbox">
                  <input
                    type="checkbox"
                    checked={selectedSites.has(site)}
                    onChange={() => handleSiteToggle(site)}
                  />
                  <span>{site}</span>
                </label>
              ))}
            </div>
          </div>

          <button
            className="btn btn-primary"
            onClick={handleTriggerJob}
            disabled={triggering || selectedSites.size === 0}
            style={{ marginTop: '1.5rem' }}
          >
            {triggering ? 'Triggering Job...' : 'Trigger Scrape Job'}
          </button>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Recent Scrape Jobs</h3>
        </div>
        <div className="card-body">
          <DataTable<ScrapeJob>
            columns={columns}
            data={jobs}
            loading={loading}
            error={error || undefined}
          />
        </div>
      </div>
    </div>
  );
};

export default ScrapeJobs;
