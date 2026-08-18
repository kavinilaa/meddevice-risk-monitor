import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Users,
  ShieldCheck,
  ShieldAlert,
  FileSpreadsheet,
  Database,
  ScrollText,
  Activity,
  ArrowRight
} from 'lucide-react';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import LoadingSpinner from '../components/LoadingSpinner';
import { adminApi } from '../services/api';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

const AdminDashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAdminStats = async () => {
      try {
        const res = await adminApi.getDashboardStats();
        setStats(res.data);
      } catch (err) {
        console.error('Error loading admin stats:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchAdminStats();
  }, []);

  const riskPieData = stats ? [
    { name: 'High Risk', value: stats.high_risk_assessments, color: '#dc2626' },
    { name: 'Low Risk', value: stats.low_risk_assessments, color: '#16a34a' },
  ] : [];

  const userPieData = stats && stats.user_distribution ? Object.keys(stats.user_distribution).map((role) => ({
    name: role === 'BIOMEDICAL_ENGINEER' ? 'Biomedical Engineer' : role === 'MAINTENANCE_TEAM' ? 'Maintenance Team' : 'Admin',
    value: stats.user_distribution[role],
    color: role === 'BIOMEDICAL_ENGINEER' ? '#0284c7' : role === 'MAINTENANCE_TEAM' ? '#0d9488' : '#64748b',
  })) : [];

  return (
    <div className="app-container">
      <Sidebar />

      <div className="main-content">
        <Header title="Administration Overview" subtitle="System metrics, user accounts, and platform audit monitor." />

        <div className="page-body">
          {loading ? (
            <LoadingSpinner message="Querying MySQL administrative statistics..." />
          ) : !stats ? (
            <div className="alert alert-danger">Unable to load administrative dashboard statistics.</div>
          ) : (
            <>
              {/* Stat Grid */}
              <div className="stat-grid">
                <div className="stat-card">
                  <div className="stat-icon primary">
                    <Users size={24} />
                  </div>
                  <div>
                    <div className="stat-value">{stats.total_users}</div>
                    <div className="stat-label">Total Registered Users ({stats.active_users} active)</div>
                  </div>
                </div>

                <div className="stat-card">
                  <div className="stat-icon teal">
                    <FileSpreadsheet size={24} />
                  </div>
                  <div>
                    <div className="stat-value">{stats.total_assessments}</div>
                    <div className="stat-label">Total Predictions Evaluated</div>
                  </div>
                </div>

                <div className="stat-card">
                  <div className="stat-icon danger">
                    <ShieldAlert size={24} />
                  </div>
                  <div>
                    <div className="stat-value">{stats.high_risk_assessments}</div>
                    <div className="stat-label">High Risk Assessments</div>
                  </div>
                </div>

                <div className="stat-card">
                  <div className="stat-icon success">
                    <ShieldCheck size={24} />
                  </div>
                  <div>
                    <div className="stat-value">{stats.low_risk_assessments}</div>
                    <div className="stat-label">Low Risk Assessments</div>
                  </div>
                </div>
              </div>

              {/* MySQL Dataset Ingestion Summary */}
              <div className="card" style={{ marginBottom: '2rem' }}>
                <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Database size={18} color="var(--primary-600)" />
                  <span>Integrated MySQL Dataset Volume</span>
                </h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
                  Live counts from the Faulty Medical Devices Global Dataset tables in MySQL
                </p>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                  <div style={{ padding: '1rem', backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>Historical Events Table</span>
                    <span style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--text-primary)', display: 'block', marginTop: '2px' }}>
                      {stats.total_historical_events.toLocaleString()}
                    </span>
                  </div>

                  <div style={{ padding: '1rem', backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>Catalog Devices Table</span>
                    <span style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--text-primary)', display: 'block', marginTop: '2px' }}>
                      {stats.total_historical_devices.toLocaleString()}
                    </span>
                  </div>

                  <div style={{ padding: '1rem', backgroundColor: 'var(--bg-app)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>Manufacturers Table</span>
                    <span style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--text-primary)', display: 'block', marginTop: '2px' }}>
                      {stats.total_historical_manufacturers.toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>

              {/* Charts & Quick Navigation Grid */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
                {/* Risk Distribution Chart */}
                <div className="card" style={{ height: '300px', display: 'flex', flexDirection: 'column' }}>
                  <h3 className="card-title">Assessment Risk Distribution</h3>
                  {stats.total_assessments > 0 ? (
                    <div style={{ flex: 1, minHeight: 0 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie data={riskPieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={4} dataKey="value">
                            {riskPieData.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                          </Pie>
                          <Tooltip />
                          <Legend />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                  ) : (
                    <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                      No assessments submitted yet.
                    </div>
                  )}
                </div>

                {/* User Distribution Chart */}
                <div className="card" style={{ height: '300px', display: 'flex', flexDirection: 'column' }}>
                  <h3 className="card-title">Registered User Roles</h3>
                  <div style={{ flex: 1, minHeight: 0 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie data={userPieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={4} dataKey="value">
                          {userPieData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip />
                        <Legend />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>

              {/* Quick Navigation Cards */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem' }}>
                <Link to="/admin/users" className="card" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div>
                    <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>Manage Users</h4>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Activate, deactivate, and review user activity</p>
                  </div>
                  <ArrowRight size={18} color="var(--primary-600)" />
                </Link>

                <Link to="/admin/predictions" className="card" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div>
                    <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>All Predictions</h4>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Inspect global machine learning assessments</p>
                  </div>
                  <ArrowRight size={18} color="var(--primary-600)" />
                </Link>

                <Link to="/admin/logs" className="card" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div>
                    <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>Audit Trail</h4>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Monitor logins, signups, and admin events</p>
                  </div>
                  <ArrowRight size={18} color="var(--primary-600)" />
                </Link>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
