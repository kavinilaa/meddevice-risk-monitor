import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Activity,
  Sparkles,
  Layers,
  ChevronDown,
  ChevronUp,
  AlertCircle
} from 'lucide-react';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import RiskScoreGauge from '../components/RiskScoreGauge';
import RiskBadge from '../components/RiskBadge';
import RiskFactorsList from '../components/RiskFactorsList';
import MaintenanceBox from '../components/MaintenanceBox';
import RiskComparisonChart from '../charts/RiskComparisonChart';
import LoadingSpinner from '../components/LoadingSpinner';
import { predictionApi } from '../services/api';
import { useAuth } from '../context/AuthContext';

const PredictionDetails = () => {
  const { id } = useParams();
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showModelFeatures, setShowModelFeatures] = useState(true);
  const { isAdmin } = useAuth();

  useEffect(() => {
    const fetchDetails = async () => {
      try {
        const res = await predictionApi.getById(id);
        setPrediction(res.data);
      } catch (err) {
        console.error('Error fetching prediction details:', err);
        setError('Unable to load assessment details or access denied.');
      } finally {
        setLoading(false);
      }
    };
    fetchDetails();
  }, [id]);

  return (
    <div className="app-container">
      <Sidebar />

      <div className="main-content">
        <Header
          title="Risk Assessment Details"
          subtitle={`Inspection record #${id}`}
        />

        <div className="page-body">
          <div style={{ marginBottom: '1.5rem' }}>
            <Link
              to={isAdmin ? '/admin/predictions' : '/predictions'}
              className="btn btn-secondary"
              style={{ fontSize: '0.85rem', padding: '0.45rem 0.9rem' }}
            >
              <ArrowLeft size={16} />
              <span>Back to Assessments</span>
            </Link>
          </div>

          {loading ? (
            <LoadingSpinner message="Retrieving assessment record..." />
          ) : error || !prediction ? (
            <div className="alert alert-danger">
              <AlertCircle size={18} />
              <span>{error || 'Assessment not found.'}</span>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
              {/* Header Overview Card */}
              <div className="card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '1rem' }}>
                  <div>
                    <span style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--primary-600)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      Assessment Summary
                    </span>
                    <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)', marginTop: '0.2rem' }}>
                      {prediction.name_manufacturer} &bull; {prediction.classification}
                    </h2>
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      Evaluated on: {new Date(prediction.created_at).toLocaleString()}
                    </p>
                  </div>
                  <RiskBadge riskLevel={prediction.risk_level} size="large" />
                </div>

                {/* Score Gauge & Volume Chart Grid */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem', marginBottom: '1.5rem' }}>
                  <RiskScoreGauge
                    scorePercentage={prediction.risk_percentage}
                    riskLevel={prediction.risk_level}
                  />
                  <RiskComparisonChart
                    eventCount={prediction.event_count}
                    manufacturerEventCount={prediction.manufacturer_event_count}
                    riskScore={prediction.risk_score}
                  />
                </div>

                {/* Explanation */}
                <div style={{
                  backgroundColor: 'var(--bg-app)',
                  padding: '1.25rem 1.5rem',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-subtle)',
                  marginBottom: '1.5rem',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                    <Sparkles size={18} color="var(--primary-600)" />
                    <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                      Model-Based Assessment Explanation
                    </h4>
                  </div>
                  <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                    {prediction.explanation}
                  </p>
                </div>

                {/* Contributing Risk Factors */}
                <div style={{ marginBottom: '1.5rem' }}>
                  <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.75rem' }}>
                    Contributing Risk Factors
                  </h4>
                  <RiskFactorsList factors={prediction.risk_factors} />
                </div>

                {/* Maintenance Recommendation */}
                <MaintenanceBox
                  recommendation={prediction.maintenance_recommendation}
                  riskLevel={prediction.risk_level}
                />
              </div>

              {/* MODEL TRANSPARENCY SECTION: ALL 13 FEATURES USED */}
              <div className="card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Layers size={18} color="var(--primary-600)" />
                    <h3 className="card-title" style={{ marginBottom: 0 }}>
                      13 Model Features Used (Pipeline Transparency)
                    </h3>
                  </div>
                  <button
                    type="button"
                    onClick={() => setShowModelFeatures(!showModelFeatures)}
                    className="btn btn-secondary"
                    style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem' }}
                  >
                    {showModelFeatures ? 'Collapse' : 'Expand'}
                  </button>
                </div>

                {showModelFeatures && (
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem', marginTop: '1rem' }}>
                    {prediction.features_used && prediction.features_used.map((f, idx) => (
                      <div key={idx} style={{
                        padding: '0.75rem 1rem',
                        backgroundColor: 'var(--bg-app)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: 'var(--radius-sm)',
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '0.2rem' }}>
                          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)' }}>
                            {idx + 1}. {f.feature_name}
                          </span>
                          <span style={{
                            fontSize: '0.65rem',
                            fontWeight: 700,
                            padding: '0.1rem 0.4rem',
                            borderRadius: '4px',
                            backgroundColor: f.source.includes('MySQL') ? 'var(--teal-50)' : 'var(--primary-50)',
                            color: f.source.includes('MySQL') ? 'var(--teal-700)' : 'var(--primary-700)',
                            border: '1px solid var(--border-subtle)',
                          }}>
                            {f.source}
                          </span>
                        </div>
                        <span style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-primary)', display: 'block', wordBreak: 'break-word' }}>
                          {String(f.value)}
                        </span>
                        <span style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                          ML Feature: {f.feature}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PredictionDetails;
