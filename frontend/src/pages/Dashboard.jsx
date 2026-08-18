import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Activity,
  ShieldPlus,
  ShieldAlert,
  ShieldCheck,
  Clock,
  ArrowRight,
  Eye,
  FileSpreadsheet
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { predictionApi } from '../services/api';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import RiskBadge from '../components/RiskBadge';
import EmptyState from '../components/EmptyState';
import LoadingSpinner from '../components/LoadingSpinner';

const Dashboard = () => {
  const { user } = useAuth();
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUserAssessments = async () => {
      try {
        const res = await predictionApi.getAll({ limit: 10 });
        setPredictions(res.data);
      } catch (err) {
        console.error('Error fetching assessments:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchUserAssessments();
  }, []);

  const totalAssessments = predictions.length;
  const highRiskCount = predictions.filter((p) => p.risk_level === 'HIGH').length;
  const lowRiskCount = predictions.filter((p) => p.risk_level === 'LOW').length;
  const latestAssessment = predictions.length > 0 ? predictions[0] : null;

  return (
    <div className="app-container">
      <Sidebar />

      <div className="main-content">
        <Header
          title="Operational Risk Dashboard"
          subtitle={`Logged in as ${user?.role === 'BIOMEDICAL_ENGINEER' ? 'Biomedical Engineer' : 'Maintenance Team Member'}`}
        />

        <div className="page-body">
          {/* Welcome Banner */}
          <div style={{
            backgroundColor: '#ffffff',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '1.5rem',
            marginBottom: '1.75rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '1rem',
          }}>
            <div>
              <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                Welcome back, {user?.full_name}
              </h2>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                Run new XGBoost risk assessments or review historical medical-device performance.
              </p>
            </div>
            <Link to="/assessment" className="btn btn-primary">
              <ShieldPlus size={18} />
              <span>New Risk Assessment</span>
            </Link>
          </div>

          {loading ? (
            <LoadingSpinner message="Retrieving assessment records from database..." />
          ) : totalAssessments === 0 ? (
            <EmptyState
              icon={Activity}
              title="No risk assessments yet"
              description="Create your first assessment to see your medical device risk prediction results."
              actionText="New Risk Assessment"
              actionLink="/assessment"
            />
          ) : (
            <>
              {/* Stat Cards with Real User Data */}
              <div className="stat-grid">
                <div className="stat-card">
                  <div className="stat-icon primary">
                    <FileSpreadsheet size={24} />
                  </div>
                  <div>
                    <div className="stat-value">{totalAssessments}</div>
                    <div className="stat-label">Total Assessments</div>
                  </div>
                </div>

                <div className="stat-card">
                  <div className="stat-icon danger">
                    <ShieldAlert size={24} />
                  </div>
                  <div>
                    <div className="stat-value">{highRiskCount}</div>
                    <div className="stat-label">High Risk Identified</div>
                  </div>
                </div>

                <div className="stat-card">
                  <div className="stat-icon success">
                    <ShieldCheck size={24} />
                  </div>
                  <div>
                    <div className="stat-value">{lowRiskCount}</div>
                    <div className="stat-label">Low Risk Verified</div>
                  </div>
                </div>

                <div className="stat-card">
                  <div className="stat-icon teal">
                    <Clock size={24} />
                  </div>
                  <div>
                    <div className="stat-value" style={{ fontSize: '1.1rem' }}>
                      {latestAssessment ? (
                        <RiskBadge riskLevel={latestAssessment.risk_level} />
                      ) : (
                        'N/A'
                      )}
                    </div>
                    <div className="stat-label">
                      Latest: {latestAssessment ? new Date(latestAssessment.created_at).toLocaleDateString() : 'None'}
                    </div>
                  </div>
                </div>
              </div>

              {/* Recent Assessments Table */}
              <div className="card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
                  <div>
                    <h3 className="card-title">Recent Risk Assessments</h3>
                    <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>
                      Evaluations performed under your account
                    </p>
                  </div>
                  <Link to="/predictions" className="btn btn-secondary" style={{ fontSize: '0.825rem', padding: '0.4rem 0.85rem' }}>
                    <span>View All History</span>
                    <ArrowRight size={15} />
                  </Link>
                </div>

                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Date & Time</th>
                        <th>Manufacturer</th>
                        <th>Device Classification</th>
                        <th>Risk Class</th>
                        <th>Risk Score</th>
                        <th>Risk Level</th>
                        <th style={{ textAlign: 'right' }}>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {predictions.map((p) => (
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
                          <td style={{ fontWeight: 700 }}>
                            {p.risk_percentage}%
                          </td>
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
                              <span>View Details</span>
                            </Link>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
