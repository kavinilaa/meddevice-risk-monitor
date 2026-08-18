import React from 'react';
import { ShieldCheck, AlertTriangle } from 'lucide-react';

const RiskBadge = ({ riskLevel, size = 'normal' }) => {
  const isHigh = String(riskLevel).toUpperCase() === 'HIGH';

  const style = {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '0.35rem',
    fontWeight: 700,
    borderRadius: 'var(--radius-full)',
    textTransform: 'uppercase',
    letterSpacing: '0.04em',
    fontSize: size === 'large' ? '0.875rem' : '0.75rem',
    padding: size === 'large' ? '0.4rem 0.9rem' : '0.25rem 0.65rem',
    backgroundColor: isHigh ? 'var(--risk-high-bg)' : 'var(--risk-low-bg)',
    color: isHigh ? 'var(--risk-high-text)' : 'var(--risk-low-text)',
    border: `1px solid ${isHigh ? 'var(--risk-high-border)' : 'var(--risk-low-border)'}`,
  };

  return (
    <span style={style}>
      {isHigh ? <AlertTriangle size={size === 'large' ? 16 : 13} /> : <ShieldCheck size={size === 'large' ? 16 : 13} />}
      {isHigh ? 'High Risk' : 'Low Risk'}
    </span>
  );
};

export default RiskBadge;
