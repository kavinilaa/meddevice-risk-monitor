import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Activity,
  ShieldCheck,
  Brain,
  Wrench,
  History,
  Lock,
  Layers,
  Database,
  ArrowRight,
  CheckCircle2,
  FileText
} from 'lucide-react';
import Navbar from '../components/Navbar';
import { metadataApi } from '../services/api';

const Landing = () => {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await metadataApi.getDatasetStats();
        setStats(res.data);
      } catch (err) {
        console.warn('Could not load public dataset statistics:', err);
      }
    };
    fetchStats();
  }, []);

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: '#ffffff' }}>
      <Navbar />

      {/* Hero Section */}
      <section style={{
        padding: '5rem 1.5rem 4rem',
        backgroundColor: 'var(--bg-app)',
        borderBottom: '1px solid var(--border-subtle)',
        textAlign: 'center',
      }}>
        <div style={{ maxWidth: '900px', margin: '0 auto' }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.4rem',
            padding: '0.35rem 0.85rem',
            borderRadius: 'var(--radius-full)',
            backgroundColor: 'var(--primary-50)',
            color: 'var(--primary-700)',
            fontSize: '0.8rem',
            fontWeight: 700,
            marginBottom: '1.25rem',
            border: '1px solid var(--primary-100)',
          }}>
            <Activity size={15} />
            <span>XGBoost Machine Learning &bull; Clinical Decision Support</span>
          </div>

          <h1 style={{
            fontSize: '2.75rem',
            fontWeight: 800,
            color: 'var(--text-primary)',
            lineHeight: 1.2,
            marginBottom: '1.25rem',
            letterSpacing: '-0.03em',
          }}>
            Assess Medical Device Risk Before It Becomes a Maintenance Problem
          </h1>

          <p style={{
            fontSize: '1.15rem',
            color: 'var(--text-secondary)',
            lineHeight: 1.6,
            maxWidth: '750px',
            margin: '0 auto 2.25rem',
          }}>
            Use historical medical-device characteristics and a trained machine-learning model to assess device risk and support maintenance decisions.
          </p>

          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            <Link to="/signup" className="btn btn-primary" style={{ padding: '0.85rem 1.75rem', fontSize: '1rem' }}>
              <span>Get Started &bull; Create Account</span>
              <ArrowRight size={18} />
            </Link>
            <Link to="/login" className="btn btn-secondary" style={{ padding: '0.85rem 1.75rem', fontSize: '1rem' }}>
              <span>Sign In</span>
            </Link>
          </div>
        </div>
      </section>

      {/* Real Dataset Statistics from MySQL */}
      {stats && (
        <section style={{ padding: '2.5rem 1.5rem', backgroundColor: '#ffffff', borderBottom: '1px solid var(--border-subtle)' }}>
          <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
            <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Ingested MySQL Knowledge Base
              </span>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '0.2rem' }}>
                Real Dataset Integration (Global Medical Device Database)
              </h3>
            </div>

            <div className="stat-grid" style={{ marginBottom: 0 }}>
              <div className="stat-card">
                <div className="stat-icon primary">
                  <Activity size={24} />
                </div>
                <div>
                  <div className="stat-value">{stats.total_events?.toLocaleString()}</div>
                  <div className="stat-label">Historical Event Records</div>
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-icon teal">
                  <Database size={24} />
                </div>
                <div>
                  <div className="stat-value">{stats.total_devices?.toLocaleString()}</div>
                  <div className="stat-label">Cataloged Medical Devices</div>
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-icon success">
                  <Layers size={24} />
                </div>
                <div>
                  <div className="stat-value">{stats.total_manufacturers?.toLocaleString()}</div>
                  <div className="stat-label">Device Manufacturers</div>
                </div>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* How It Works Section */}
      <section style={{ padding: '4rem 1.5rem', backgroundColor: 'var(--bg-app)', borderBottom: '1px solid var(--border-subtle)' }}>
        <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--primary-700)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Operational Workflow
            </span>
            <h2 style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--text-primary)', marginTop: '0.25rem' }}>
              How It Works
            </h2>
            <p style={{ fontSize: '0.95rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
              Four structured steps to evaluate medical device risk profile and support biomedical maintenance
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.5rem' }}>
            {[
              {
                step: '01',
                title: 'Enter Device Information',
                desc: 'Input 13 standardized device, manufacturer, regulatory class, and historical parameters.',
                icon: FileText,
              },
              {
                step: '02',
                title: 'Assess Risk',
                desc: 'FastAPI passes inputs to the pre-trained XGBoost pipeline to compute precise risk probability.',
                icon: Brain,
              },
              {
                step: '03',
                title: 'Understand Risk Factors',
                desc: 'SHAP explainability identifies top contributing factors driving elevated or reduced risk.',
                icon: ShieldCheck,
              },
              {
                step: '04',
                title: 'Review Recommendations',
                desc: 'Receive tailored preventive maintenance protocols and clinical decision-support instructions.',
                icon: Wrench,
              },
            ].map((s, idx) => (
              <div key={idx} className="card" style={{ position: 'relative' }}>
                <span style={{
                  fontSize: '0.75rem',
                  fontWeight: 800,
                  color: 'var(--primary-600)',
                  backgroundColor: 'var(--primary-50)',
                  padding: '0.2rem 0.5rem',
                  borderRadius: '4px',
                  display: 'inline-block',
                  marginBottom: '1rem',
                }}>
                  STEP {s.step}
                </span>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
                  {s.title}
                </h3>
                <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                  {s.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Platform Features Section */}
      <section style={{ padding: '4rem 1.5rem', backgroundColor: '#ffffff', borderBottom: '1px solid var(--border-subtle)' }}>
        <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--primary-700)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              System Capabilities
            </span>
            <h2 style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--text-primary)', marginTop: '0.25rem' }}>
              Engineered for Healthcare Quality & Compliance
            </h2>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
            {[
              {
                icon: Brain,
                title: 'XGBoost Risk Prediction',
                desc: 'Trained on 13 historical event features to estimate binary risk and probability with calibrated scale weights.',
              },
              {
                icon: Activity,
                title: 'Model-Derived Risk Score',
                desc: 'Displays exact model probability percentage without arbitrary multipliers or hardcoded scores.',
              },
              {
                icon: ShieldCheck,
                title: 'Explainable AI Insights',
                desc: 'SHAP TreeExplainer attributes specific contributions to risk classification, event frequency, and implant status.',
              },
              {
                icon: Wrench,
                title: 'Maintenance Decision Support',
                desc: 'Provides structured inspection intervals, CMMS logging guides, and clinical protocol reminders.',
              },
              {
                icon: History,
                title: 'Assessment Audit History',
                desc: 'Complete chronological history isolated per biomedical engineer with full detail modal review.',
              },
              {
                icon: Lock,
                title: 'Role-Based Access Control',
                desc: 'Strict JWT authorization for Biomedical Engineers, Maintenance Teams, and Platform Administrators.',
              },
            ].map((f, idx) => {
              const IconComp = f.icon;
              return (
                <div key={idx} style={{ display: 'flex', gap: '1rem', padding: '1rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{
                    width: '40px',
                    height: '40px',
                    borderRadius: 'var(--radius-sm)',
                    backgroundColor: 'var(--primary-50)',
                    color: 'var(--primary-600)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                  }}>
                    <IconComp size={20} />
                  </div>
                  <div>
                    <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
                      {f.title}
                    </h4>
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                      {f.desc}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Model & Features Info Section */}
      <section style={{ padding: '3.5rem 1.5rem', backgroundColor: 'var(--bg-app)', borderBottom: '1px solid var(--border-subtle)' }}>
        <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
          <div className="card">
            <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
              Model Architecture & The 13 Features
            </h3>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '1.25rem' }}>
              The system utilizes an XGBoost binary classification model trained on the Faulty Medical Devices Global Dataset.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '0.75rem' }}>
              {[
                '1. type', '2. status', '3. classification', '4. risk_class',
                '5. country_event', '6. country_device', '7. implanted', '8. name_manufacturer',
                '9. quantity_in_commerce', '10. event_count', '11. manufacturer_event_count',
                '12. event_year', '13. event_month'
              ].map((feat, idx) => (
                <div key={idx} style={{
                  padding: '0.5rem 0.75rem',
                  backgroundColor: '#ffffff',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.825rem',
                  fontFamily: 'var(--font-mono)',
                  color: 'var(--text-primary)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                }}>
                  <CheckCircle2 size={14} color="var(--primary-600)" />
                  <span>{feat}</span>
                </div>
              ))}
            </div>

            <div className="disclaimer-box">
              <strong>DECISION SUPPORT NOTICE:</strong> This platform estimates historical risk patterns for maintenance decision support. It does not replace physical inspection, manufacturer instructions, or professional biomedical engineering judgment.
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer style={{ padding: '2rem 1.5rem', backgroundColor: '#ffffff', textAlign: 'center', fontSize: '0.825rem', color: 'var(--text-muted)' }}>
        <p>&copy; 2026 MedDevice Risk Monitor &bull; Medical Device Failure Prediction & Risk Assessment Platform.</p>
        <p style={{ marginTop: '0.25rem' }}>AI & Data Science Student Project &bull; Built with FastAPI, XGBoost, MySQL & React.</p>
      </footer>
    </div>
  );
};

export default Landing;
