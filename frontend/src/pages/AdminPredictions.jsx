import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  FileSpreadsheet,
  Search,
  Filter,
  Eye,
  ArrowUpDown
} from 'lucide-react';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import RiskBadge from '../components/RiskBadge';
import EmptyState from '../components/EmptyState';
import LoadingSpinner from '../components/LoadingSpinner';
import { adminApi } from '../services/api';

const AdminPredictions = () => {
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [riskFilter, setRiskFilter] = useState('');
  const [sortOrder, setSortOrder] = useState('desc');

  const fetchGlobalPredictions = async () => {
    setLoading(true);
    try {
      const params = {};
      if (riskFilter) params.risk_level = riskFilter;
      if (search.trim()) params.search = search.trim();
      const res = await adminApi.getPredictions(params);
      setPredictions(res.data);
    } catch (err) {
      console.error('Error fetching global predictions:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGlobalPredictions();
  }, [riskFilter]);

  const handleSearch = (e) => {
    e.preventDefault();
    fetchGlobalPredictions();
  };

  const sorted = [...predictions].sort((a, b) => {
    const da = new Date(a.created_at).getTime();
    const db = new Date(b.created_at).getTime();
    return sortOrder === 'desc' ? db - da : da - db;
  });

  return (
    <div className="app-container">
      <Sidebar />

      <div className="main-content">
        <Header title="Global Prediction Monitoring" subtitle="Audit all medical device risk assessments across the entire platform." />

        <div className="page-body">
          {/* Filter Bar */}
          <div className="card" style={{ padding: '1.25rem', marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
              <form onSubmit={handleSearch} style={{ display: 'flex', gap: '0.5rem', flex: 1, minWidth: '260px', maxWidth: '420px' }}>
                <input
                  type="text"
                  className="form-control"
                  placeholder="Search manufacturer, user, classification..."
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
              </div>
            </div>
          </div>

          {/* Predictions Table */}
          {loading ? (
            <LoadingSpinner message="Retrieving platform assessment records..." />
          ) : sorted.length === 0 ? (
            <EmptyState
              icon={FileSpreadsheet}
              title="No assessments have been created yet"
              description="When biomedical engineers or maintenance personnel submit assessments, they will appear in this administrative monitor."
            />
          ) : (
            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
              <div className="table-container" style={{ border: 'none', borderRadius: 0 }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Assessed By</th>
                      <th>Role</th>
                      <th>Manufacturer</th>
                      <th>Classification</th>
                      <th>Prediction</th>
                      <th>Risk Score</th>
                      <th>Risk Level</th>
                      <th style={{ textAlign: 'right' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sorted.map((p) => (
                      <tr key={p.id}>
                        <td style={{ whiteSpace: 'nowrap', fontSize: '0.825rem' }}>
                          {new Date(p.created_at).toLocaleString()}
                        </td>
                        <td style={{ fontWeight: 600 }}>{p.user_name || `User #${p.user_id}`}</td>
                        <td>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                            {p.user_role === 'BIOMEDICAL_ENGINEER' ? 'Biomedical Engineer' : p.user_role === 'MAINTENANCE_TEAM' ? 'Maintenance Team' : p.user_role}
                          </span>
                        </td>
                        <td style={{ fontWeight: 600 }}>{p.name_manufacturer}</td>
                        <td>{p.classification}</td>
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
                            <span>Details</span>
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

export default AdminPredictions;
