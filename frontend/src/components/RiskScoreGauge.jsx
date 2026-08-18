import React from 'react';

const RiskScoreGauge = ({ scorePercentage, riskLevel }) => {
  const pct = Math.max(0, Math.min(100, Number(scorePercentage) || 0));
  const isHigh = String(riskLevel).toUpperCase() === 'HIGH' || pct >= 50;

  const barColor = isHigh ? 'var(--risk-high-solid)' : 'var(--risk-low-solid)';
  const trackBg = isHigh ? 'var(--risk-high-bg)' : 'var(--risk-low-bg)';

  return (
    <div style={{
      backgroundColor: 'var(--bg-surface)',
      border: '1px solid var(--border-subtle)',
      borderRadius: 'var(--radius-md)',
      padding: '1.5rem',
      display: 'flex',
      flexDirection: 'column',
      gap: '0.75rem',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
        <div>
          <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Model Estimated Risk Score
          </span>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '2px' }}>
            Historical probability derived directly from XGBoost pipeline
          </p>
        </div>
        <div style={{ textAlign: 'right' }}>
          <span style={{ fontSize: '2.25rem', fontWeight: 800, color: barColor, lineHeight: 1 }}>
            {pct.toFixed(1)}%
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      <div style={{
        width: '100%',
        height: '14px',
        backgroundColor: trackBg,
        borderRadius: 'var(--radius-full)',
        overflow: 'hidden',
        border: '1px solid var(--border-subtle)',
        position: 'relative',
      }}>
        <div style={{
          width: `${pct}%`,
          height: '100%',
          backgroundColor: barColor,
          borderRadius: 'var(--radius-full)',
          transition: 'width 0.6s cubic-bezier(0.4, 0, 0.2, 1)',
        }} />
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
        <span>0% (Minimum Risk)</span>
        <span style={{ fontWeight: 600 }}>50% Decision Threshold</span>
        <span>100% (Maximum Risk)</span>
      </div>
    </div>
  );
};

export default RiskScoreGauge;
// import React from 'react';

// const RiskScoreGauge = ({ scorePercentage, riskLevel }) => {
//   // Keep the actual model percentage for the progress bar
//   const pct = Math.max(0, Math.min(100, Number(scorePercentage) || 0));

//   // Round ONLY the displayed percentage
//   const displayPct = Math.round(pct);

//   const isHigh =
//     String(riskLevel).toUpperCase() === 'HIGH' || pct >= 50;

//   const barColor = isHigh
//     ? 'var(--risk-high-solid)'
//     : 'var(--risk-low-solid)';

//   const trackBg = isHigh
//     ? 'var(--risk-high-bg)'
//     : 'var(--risk-low-bg)';

//   return (
//     <div
//       style={{
//         backgroundColor: 'var(--bg-surface)',
//         border: '1px solid var(--border-subtle)',
//         borderRadius: 'var(--radius-md)',
//         padding: '1.5rem',
//         display: 'flex',
//         flexDirection: 'column',
//         gap: '0.75rem',
//       }}
//     >
//       <div
//         style={{
//           display: 'flex',
//           justifyContent: 'space-between',
//           alignItems: 'baseline',
//         }}
//       >
//         <div>
//           <span
//             style={{
//               fontSize: '0.85rem',
//               fontWeight: 600,
//               color: 'var(--text-muted)',
//               textTransform: 'uppercase',
//               letterSpacing: '0.04em',
//             }}
//           >
//             Model Estimated Risk Score
//           </span>

//           <p
//             style={{
//               fontSize: '0.8rem',
//               color: 'var(--text-muted)',
//               marginTop: '2px',
//             }}
//           >
//             Historical probability derived directly from XGBoost pipeline
//           </p>
//         </div>

//         <div style={{ textAlign: 'right' }}>
//           <span
//             style={{
//               fontSize: '2.25rem',
//               fontWeight: 800,
//               color: barColor,
//               lineHeight: 1,
//             }}
//           >
//             {displayPct}%
//           </span>
//         </div>
//       </div>

//       {/* Progress Bar */}
//       <div
//         style={{
//           width: '100%',
//           height: '14px',
//           backgroundColor: trackBg,
//           borderRadius: 'var(--radius-full)',
//           overflow: 'hidden',
//           border: '1px solid var(--border-subtle)',
//           position: 'relative',
//         }}
//       >
//         <div
//           style={{
//             width: `${pct}%`,
//             height: '100%',
//             backgroundColor: barColor,
//             borderRadius: 'var(--radius-full)',
//             transition: 'width 0.6s cubic-bezier(0.4, 0, 0.2, 1)',
//           }}
//         />
//       </div>

//       <div
//         style={{
//           display: 'flex',
//           justifyContent: 'space-between',
//           fontSize: '0.75rem',
//           color: 'var(--text-muted)',
//         }}
//       >
//         <span>0% (Minimum Risk)</span>

//         <span style={{ fontWeight: 600 }}>
//           50% Decision Threshold
//         </span>

//         <span>100% (Maximum Risk)</span>
//       </div>
//     </div>
//   );
// };

// export default RiskScoreGauge;