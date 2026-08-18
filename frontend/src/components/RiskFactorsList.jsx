import React from 'react';
import { ArrowUpRight, ArrowDownRight, Minus, HelpCircle } from 'lucide-react';

const RiskFactorsList = ({ factors = [] }) => {
  if (!factors || factors.length === 0) {
    return (
      <div style={{ padding: '1rem', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
        No specific factor anomalies identified for this profile.
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      {factors.map((item, idx) => {
        const isElevated = item.impact === 'ELEVATED_RISK';
        const isReduced = item.impact === 'REDUCED_RISK';

        let icon = <Minus size={16} color="var(--text-muted)" />;
        let badgeBg = 'var(--bg-subtle)';
        let badgeText = 'var(--text-secondary)';
        let badgeLabel = 'Neutral';

        if (isElevated) {
          icon = <ArrowUpRight size={16} color="var(--risk-high-solid)" />;
          badgeBg = 'var(--risk-high-bg)';
          badgeText = 'var(--risk-high-text)';
          badgeLabel = 'Elevated Risk Impact';
        } else if (isReduced) {
          icon = <ArrowDownRight size={16} color="var(--risk-low-solid)" />;
          badgeBg = 'var(--risk-low-bg)';
          badgeText = 'var(--risk-low-text)';
          badgeLabel = 'Reduced Risk Impact';
        }

        return (
          <div
            key={idx}
            style={{
              display: 'flex',
              flexDirection: 'column',
              padding: '1rem',
              backgroundColor: '#ffffff',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              gap: '0.35rem',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                {icon}
                <span style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--text-primary)' }}>
                  {item.feature_name || item.feature}
                </span>
                <span style={{
                  fontSize: '0.8rem',
                  fontFamily: 'var(--font-mono)',
                  backgroundColor: 'var(--bg-subtle)',
                  padding: '0.15rem 0.4rem',
                  borderRadius: '4px',
                  color: 'var(--text-secondary)',
                }}>
                  {String(item.value)}
                </span>
              </div>
              <span style={{
                fontSize: '0.725rem',
                fontWeight: 700,
                padding: '0.2rem 0.5rem',
                borderRadius: 'var(--radius-full)',
                backgroundColor: badgeBg,
                color: badgeText,
                textTransform: 'uppercase',
              }}>
                {badgeLabel}
              </span>
            </div>
            <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', lineHeight: 1.4, marginTop: '2px' }}>
              {item.description}
            </p>
          </div>
        );
      })}
    </div>
  );
};

export default RiskFactorsList;
