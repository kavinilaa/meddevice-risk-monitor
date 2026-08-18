import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const RiskComparisonChart = ({ eventCount = 0, manufacturerEventCount = 0, riskScore = 0 }) => {
  const data = [
    { name: 'Device Events', value: Number(eventCount) || 0, color: '#0284c7' },
    { name: 'Mfr Total Events', value: Number(manufacturerEventCount) || 0, color: '#0d9488' },
  ];

  return (
    <div style={{
      backgroundColor: 'var(--bg-surface)',
      border: '1px solid var(--border-subtle)',
      borderRadius: 'var(--radius-md)',
      padding: '1.25rem',
      height: '240px',
      display: 'flex',
      flexDirection: 'column',
    }}>
      <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.75rem' }}>
        Historical Event Volume Context
      </span>
      <div style={{ flex: 1, width: '100%', minHeight: 0 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
            <XAxis type="number" fontSize={11} stroke="var(--text-muted)" />
            <YAxis type="category" dataKey="name" fontSize={11} stroke="var(--text-secondary)" width={100} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#ffffff',
                border: '1px solid var(--border-subtle)',
                borderRadius: '6px',
                fontSize: '12px',
              }}
            />
            <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={20}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default RiskComparisonChart;
