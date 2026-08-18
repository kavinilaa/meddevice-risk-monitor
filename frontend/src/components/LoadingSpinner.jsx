import React from 'react';
import { Loader2 } from 'lucide-react';

const LoadingSpinner = ({ fullScreen = false, message = 'Loading...' }) => {
  if (fullScreen) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        backgroundColor: 'var(--bg-app)',
        gap: '1rem',
      }}>
        <Loader2 size={36} className="spinner-icon" style={{ animation: 'spin 1s linear infinite', color: 'var(--primary-600)' }} />
        <p style={{ fontSize: '0.95rem', color: 'var(--text-muted)', fontWeight: 500 }}>{message}</p>
        <style>{`
          @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '0.75rem',
      padding: '2rem',
      color: 'var(--text-muted)',
    }}>
      <Loader2 size={24} style={{ animation: 'spin 1s linear infinite', color: 'var(--primary-600)' }} />
      <span style={{ fontSize: '0.9rem', fontWeight: 500 }}>{message}</span>
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default LoadingSpinner;
