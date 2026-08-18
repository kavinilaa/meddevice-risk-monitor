import React from 'react';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';
import { UserCircle, Shield, Wrench, ShieldCheck } from 'lucide-react';

const Header = ({ title, subtitle }) => {
  const { user, isAdmin } = useAuth();

  const getRoleIcon = () => {
    if (user?.role === 'BIOMEDICAL_ENGINEER') return <Shield size={14} />;
    if (user?.role === 'MAINTENANCE_TEAM') return <Wrench size={14} />;
    return <ShieldCheck size={14} />;
  };

  const getRoleLabel = () => {
    if (user?.role === 'BIOMEDICAL_ENGINEER') return 'Biomedical Engineer';
    if (user?.role === 'MAINTENANCE_TEAM') return 'Maintenance Team';
    if (user?.role === 'ADMIN') return 'Administrator';
    return user?.role || 'Operational User';
  };

  return (
    <header style={{
      backgroundColor: '#ffffff',
      borderBottom: '1px solid var(--border-subtle)',
      padding: '1rem 2rem',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
    }}>
      <div>
        {title && <h1 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)' }}>{title}</h1>}
        {subtitle && <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>{subtitle}</p>}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div style={{ textAlign: 'right' }}>
          <p style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.2 }}>
            {user?.full_name}
          </p>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.725rem', color: 'var(--primary-700)', fontWeight: 600, marginTop: '2px' }}>
            {getRoleIcon()}
            <span>{getRoleLabel()}</span>
          </div>
        </div>

        <Link
          to={isAdmin ? '/admin/profile' : '/profile'}
          style={{
            width: '36px',
            height: '36px',
            borderRadius: '50%',
            backgroundColor: 'var(--primary-50)',
            color: 'var(--primary-600)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            textDecoration: 'none',
          }}
          title="View Profile"
        >
          <UserCircle size={22} />
        </Link>
      </div>
    </header>
  );
};

export default Header;
