import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { History, Activity, AlertCircle, TrendingUp, Minus, Info } from 'lucide-react';
import { metadataApi } from '../services/api';

const TREND_STYLES = {
  Stable: { badgeClass: 'badge-neutral', icon: Minus, arrows: '' },
  Increasing: { badgeClass: 'badge-warning', icon: TrendingUp, arrows: '↑' },
  'Rapidly Increasing': { badgeClass: 'badge-high', icon: TrendingUp, arrows: '↑↑' },
};

const RiskTrendTimeline = ({ deviceId, deviceName }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [data, setData] = useState(null);

  useEffect(() => {
    if (!deviceId) {
      setData(null);
      setError('');
      return;
    }

    let cancelled = false;
    const fetchHistory = async () => {
      setIsLoading(true);
      setError('');
      try {
        const res = await metadataApi.getDeviceHistory(deviceId);
        if (!cancelled) setData(res.data);
      } catch (err) {
        if (!cancelled) {
          const detail = err.response && err.response.data && err.response.data.detail;
          setError(detail || 'Failed to load historical event trend for this device.');
        }
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    };

    fetchHistory();
    return () => { cancelled = true; };
  }, [deviceId]);

  const cardStyle = {
    backgroundColor: 'var(--bg-surface)',
    border: '1px solid var(--border-subtle)',
    borderRadius: 'var(--radius-md)',
    padding: '1.5rem',
  };

  const headerBlock = (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '1rem' }}>
      <div style={{
        width: '36px',
        height: '36px',
        borderRadius: 'var(--radius-sm)',
        backgroundColor: 'var(--primary-50)',
        color: 'var(--primary-600)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0,
      }}>
        <History size={20} />
      </div>
      <div>
        <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
          Risk Trend / Historical Timeline
        </h4>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          Historical event activity for this medical device
        </p>
      </div>
    </div>
  );

  // No device selected yet (user typed a free-text name without picking a search suggestion)
  if (!deviceId) {
    return (
      <div style={cardStyle}>
        {headerBlock}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.6rem',
          padding: '0.85rem 1rem',
          backgroundColor: 'var(--bg-app)',
          border: '1px dashed var(--border-subtle)',
          borderRadius: 'var(--radius-sm)',
          fontSize: '0.85rem',
          color: 'var(--text-muted)',
        }}>
          <Info size={16} />
          <span>Select "{deviceName || 'a device'}" from the Device Name search suggestions to view its historical event trend.</span>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div style={cardStyle}>
        {headerBlock}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
          <Activity size={16} className="animate-spin" />
          <span>Loading historical event trend...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={cardStyle}>
        {headerBlock}
        <div className="alert alert-danger" style={{ marginBottom: 0 }}>
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      </div>
    );
  }

  if (!data || !data.history || data.history.length === 0) {
    return (
      <div style={cardStyle}>
        {headerBlock}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.6rem',
          padding: '0.85rem 1rem',
          backgroundColor: 'var(--bg-app)',
          border: '1px dashed var(--border-subtle)',
          borderRadius: 'var(--radius-sm)',
          fontSize: '0.85rem',
          color: 'var(--text-muted)',
        }}>
          <Info size={16} />
          <span>{(data && data.explanation) || 'No historical event data available for this device.'}</span>
        </div>
      </div>
    );
  }

  const style = TREND_STYLES[data.trend] || TREND_STYLES.Stable;
  const TrendIcon = style.icon;
  const maxCount = Math.max(...data.history.map((p) => p.event_count), 1);

  return (
    <div style={cardStyle}>
      {headerBlock}

      <span style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        Device Risk History
      </span>

      <div style={{ height: '220px', marginTop: '0.5rem', marginBottom: '1.25rem' }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data.history} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" vertical={false} />
            <XAxis dataKey="year" fontSize={11} stroke="var(--text-muted)" />
            <YAxis
              allowDecimals={false}
              domain={[0, maxCount]}
              fontSize={11}
              stroke="var(--text-muted)"
              label={{ value: 'Event Count', angle: -90, position: 'insideLeft', fontSize: 11, fill: 'var(--text-muted)' }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#ffffff',
                border: '1px solid var(--border-subtle)',
                borderRadius: '6px',
                fontSize: '12px',
              }}
              formatter={(value) => [value, 'Events']}
              labelFormatter={(label) => `Year ${label}`}
            />
            <Line
              type="monotone"
              dataKey="event_count"
              stroke="var(--primary-600)"
              strokeWidth={2.5}
              dot={{ r: 4, fill: 'var(--primary-600)' }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
        <span className={`badge ${style.badgeClass}`}>
          <TrendIcon size={13} />
          <span>{data.trend}{style.arrows ? ` ${style.arrows}` : ''}</span>
        </span>
        <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
          {data.explanation}
        </span>
      </div>
    </div>
  );
};

export default RiskTrendTimeline;
