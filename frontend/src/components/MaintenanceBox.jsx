import React from 'react';
import { Wrench, ShieldAlert, Info } from 'lucide-react';

const MaintenanceBox = ({ recommendation, riskLevel }) => {
  const isHigh = String(riskLevel).toUpperCase() === 'HIGH';

  return (
    <div style={{
      backgroundColor: 'var(--bg-surface)',
      border: `1px solid ${isHigh ? 'var(--risk-high-border)' : 'var(--risk-low-border)'}`,
      borderRadius: 'var(--radius-md)',
      padding: '1.5rem',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '1rem' }}>
        <div style={{
          width: '36px',
          height: '36px',
          borderRadius: 'var(--radius-sm)',
          backgroundColor: isHigh ? 'var(--risk-high-bg)' : 'var(--risk-low-bg)',
          color: isHigh ? 'var(--risk-high-solid)' : 'var(--risk-low-solid)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          {isHigh ? <ShieldAlert size={20} /> : <Wrench size={20} />}
        </div>
        <div>
          <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            Recommended Maintenance Support Action
          </h4>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Decision-support protocol generated for biomedical and technical personnel
          </p>
        </div>
      </div>

      <div style={{
        whiteSpace: 'pre-line',
        fontSize: '0.875rem',
        color: 'var(--text-secondary)',
        lineHeight: 1.6,
        backgroundColor: 'var(--bg-app)',
        padding: '1rem 1.25rem',
        borderRadius: 'var(--radius-sm)',
        border: '1px solid var(--border-subtle)',
      }}>
        {recommendation}
      </div>
    </div>
  );
};

export default MaintenanceBox;
