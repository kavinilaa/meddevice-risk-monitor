import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  History,
  Search,
  Filter,
  Eye,
  ArrowUpDown,
  ShieldPlus,
  FileSpreadsheet
} from 'lucide-react';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import RiskBadge from '../components/RiskBadge';
import EmptyState from '../components/EmptyState';
import LoadingSpinner from '../components/LoadingSpinner';
import { predictionApi } from '../services/api';

const PredictionHistory = () => {
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [riskFilter, setRiskFilter] = useState('');
  const [sortOrder, setSortOrder] = useState('desc');

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const params = {};
      if (riskFilter) params.risk_level = riskFilter;
      if (search.trim()) params.search = search.trim();
      const res = await predictionApi.getAll(params);
      setPredictions(res.data);
    } catch (err) {
      console.error('Error fetching history:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [riskFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchHistory();
  };

  const sortedPredictions = [...predictions].sort((a, b) => {
    const dateA = new Date(a.created_at).getTime();
    const dateB = new Date(b.created_at).getTime();
    return sortOrder === 'desc' ? dateB - dateA : dateA - dateB;
  });

  return (
    <div className="app-container">
      <Sidebar />

      <div className="main-content">
        <Header
          title="Prediction Assessment History"
          subtitle="Review and audit your past medical device failure risk assessments."
        />

        <div className="page-body">
          {/* Controls Bar */}
          <div className="card" style={{ padding: '1.25rem', marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
              <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: '0.5rem', flex: 1, minWidth: '260px', maxWidth: '480px' }}>
                <input
                  type="text"
                  className="form-control"
                  placeholder="Search manufacturer, classification..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
                <button type="submit" className="btn btn-secondary" style={{ padding: '0.65rem 1rem' }}>
                  <Search size={16} />
                </button>
              </form>

              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <Filter size={16} color="var(--text-muted)" />
                  <select
                    className="form-control"
                    style={{ width: 'auto', padding: '0.45rem 2rem 0.45rem 0.75rem', fontSize: '0.85rem' }}
                    value={riskFilter}
                    onChange={(e) => setRiskFilter(e.target.value)}
                  >
                    <option value="">All Risk Levels</option>
                    <option value="HIGH">High Risk Only</option>
                    <option value="LOW">Low Risk Only</option>
                  </select>
                </div>

                <button
                  onClick={() => setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')}
                  className="btn btn-secondary"
                  style={{ fontSize: '0.85rem', padding: '0.45rem 0.85rem' }}
                >
                  <ArrowUpDown size={15} />
                  <span>{sortOrder === 'desc' ? 'Newest First' : 'Oldest First'}</span>
                </button>

                <Link to="/assessment" className="btn btn-primary" style={{ fontSize: '0.85rem', padding: '0.45rem 1rem' }}>
                  <ShieldPlus size={16} />
                  <span>New Assessment</span>
                </Link>
              </div>
            </div>
          </div>

          {/* Table or Empty State */}
          {loading ? (
            <LoadingSpinner message="Loading your prediction history..." />
          ) : sortedPredictions.length === 0 ? (
            <EmptyState
              icon={History}
              title="No prediction history available"
              description={search || riskFilter ? "No matching records found for the applied filters." : "You have not performed any medical device risk assessments yet."}
              actionText="New Risk Assessment"
              actionLink="/assessment"
            />
          ) : (
            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
              <div className="table-container" style={{ border: 'none', borderRadius: 0 }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Assessment Date</th>
                      <th>Manufacturer</th>
                      <th>Device Classification</th>
                      <th>Risk Class</th>
                      <th>Prediction</th>
                      <th>Risk Score</th>
                      <th>Risk Level</th>
                      <th style={{ textAlign: 'right' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedPredictions.map((p) => (
                      <tr key={p.id}>
                        <td style={{ whiteSpace: 'nowrap', fontSize: '0.825rem' }}>
                          {new Date(p.created_at).toLocaleString()}
                        </td>
                        <td style={{ fontWeight: 600 }}>{p.name_manufacturer}</td>
                        <td>{p.classification}</td>
                        <td>
                          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', backgroundColor: 'var(--bg-subtle)', padding: '0.15rem 0.4rem', borderRadius: '4px' }}>
                            Class {p.risk_class}
                          </span>
                        </td>
                        <td style={{ fontWeight: 600 }}>{p.prediction_label}</td>
                        <td style={{ fontWeight: 700 }}>{p.risk_percentage}%</td>
                        <td>
                          <RiskBadge riskLevel={p.risk_level} />
                        </td>
                        <td style={{ textAlign: 'right' }}>
                          <Link
                            to={`/predictions/${p.id}`}
                            className="btn btn-secondary"
                            style={{ padding: '0.35rem 0.75rem', fontSize: '0.8rem' }}
                          >
                            <Eye size={14} />
                            <span>View</span>
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PredictionHistory;
