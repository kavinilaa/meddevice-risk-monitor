import React, { useState, useEffect } from 'react';
import { ScrollText, Filter, Activity, Clock, ShieldCheck, User } from 'lucide-react';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import LoadingSpinner from '../components/LoadingSpinner';
import EmptyState from '../components/EmptyState';
import { adminApi } from '../services/api';

const AdminLogs = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionFilter, setActionFilter] = useState('');

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const params = {};
      if (actionFilter) params.action = actionFilter;
      const res = await adminApi.getLogs(params);
      setLogs(res.data);
    } catch (err) {
      console.error('Error fetching audit logs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [actionFilter]);

  const getActionBadgeColor = (action) => {
    switch (action) {
      case 'LOGIN':
        return { bg: 'var(--primary-50)', text: 'var(--primary-700)', border: 'var(--primary-100)' };
      case 'LOGOUT':
        return { bg: 'var(--bg-subtle)', text: 'var(--text-secondary)', border: 'var(--border-subtle)' };
      case 'SIGNUP':
        return { bg: 'var(--teal-50)', text: 'var(--teal-700)', border: 'var(--teal-600)' };
      case 'PREDICTION_CREATED':
        return { bg: 'var(--primary-50)', text: 'var(--primary-600)', border: 'var(--primary-100)' };
      case 'USER_DEACTIVATED':
        return { bg: 'var(--risk-high-bg)', text: 'var(--risk-high-text)', border: 'var(--risk-high-border)' };
      case 'USER_ACTIVATED':
        return { bg: 'var(--risk-low-bg)', text: 'var(--risk-low-text)', border: 'var(--risk-low-border)' };
      default:
        return { bg: 'var(--bg-subtle)', text: 'var(--text-secondary)', border: 'var(--border-subtle)' };
    }
  };

  return (
    <div className="app-container">
      <Sidebar />

      <div className="main-content">
        <Header title="Platform Audit Trail" subtitle="Trace user authentication, prediction creations, and security events." />

        <div className="page-body">
          {/* Controls Bar */}
          <div className="card" style={{ padding: '1.25rem', marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <ScrollText size={18} color="var(--primary-600)" />
                <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>System Event Log</span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Filter size={16} color="var(--text-muted)" />
                <select
                  className="form-control"
                  style={{ width: 'auto', padding: '0.45rem 2rem 0.45rem 0.75rem', fontSize: '0.85rem' }}
                  value={actionFilter}
                  onChange={(e) => setActionFilter(e.target.value)}
                >
                  <option value="">All Actions</option>
                  <option value="LOGIN">LOGIN</option>
                  <option value="LOGOUT">LOGOUT</option>
                  <option value="SIGNUP">SIGNUP</option>
                  <option value="PREDICTION_CREATED">PREDICTION_CREATED</option>
                  <option value="USER_ACTIVATED">USER_ACTIVATED</option>
                  <option value="USER_DEACTIVATED">USER_DEACTIVATED</option>
                  <option value="PASSWORD_CHANGED">PASSWORD_CHANGED</option>
                </select>
              </div>
            </div>
          </div>

          {/* Logs Table */}
          {loading ? (
            <LoadingSpinner message="Querying audit trail records..." />
          ) : logs.length === 0 ? (
            <EmptyState
              icon={ScrollText}
              title="No activity logs available"
              description="Platform interactions and authentication events will appear here in chronological order."
            />
          ) : (
            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
              <div className="table-container" style={{ border: 'none', borderRadius: 0 }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Timestamp</th>
                      <th>Action</th>
                      <th>User Account</th>
                      <th>Description</th>
                      <th>IP Address</th>
                    </tr>
                  </thead>
                  <tbody>
                    {logs.map((log) => {
                      const badge = getActionBadgeColor(log.action);
                      return (
                        <tr key={log.id}>
                          <td style={{ whiteSpace: 'nowrap', fontSize: '0.825rem', color: 'var(--text-muted)' }}>
                            {new Date(log.created_at).toLocaleString()}
                          </td>
                          <td>
                            <span style={{
                              display: 'inline-block',
                              fontSize: '0.725rem',
                              fontWeight: 700,
                              fontFamily: 'var(--font-mono)',
                              padding: '0.2rem 0.5rem',
                              borderRadius: '4px',
                              backgroundColor: badge.bg,
                              color: badge.text,
                              border: `1px solid ${badge.border}`,
                            }}>
                              {log.action}
                            </span>
                          </td>
                          <td style={{ fontWeight: 600 }}>
                            {log.user_email || log.user_name || 'System / Guest'}
                          </td>
                          <td style={{ fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                            {log.description}
                          </td>
                          <td style={{ fontSize: '0.8rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                            {log.ip_address || '127.0.0.1'}
                          </td>
                        </tr>
                      );
                    })}
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

export default AdminLogs;
