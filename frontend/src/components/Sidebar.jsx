import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  ShieldPlus,
  History,
  User,
  Users,
  FileSpreadsheet,
  ScrollText,
  LogOut,
  Activity,
  ShieldAlert
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const Sidebar = () => {
  const { user, isAdmin, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
  };

  const navItemStyle = ({ isActive }) => ({
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    padding: '0.75rem 1rem',
    borderRadius: 'var(--radius-sm)',
    fontSize: '0.9rem',
    fontWeight: isActive ? 700 : 500,
    color: isActive ? 'var(--primary-700)' : 'var(--text-secondary)',
    backgroundColor: isActive ? 'var(--primary-50)' : 'transparent',
    textDecoration: 'none',
    transition: 'all 0.15s ease',
    marginBottom: '0.25rem',
  });

  return (
    <aside style={{
      width: '260px',
      backgroundColor: '#ffffff',
      borderRight: '1px solid var(--border-subtle)',
      display: 'flex',
      flexDirection: 'column',
      flexShrink: 0,
      minHeight: '100vh',
    }}>
      {/* Brand Header */}
      <div style={{
        padding: '1.25rem 1.5rem',
        borderBottom: '1px solid var(--border-subtle)',
        display: 'flex',
        alignItems: 'center',
        gap: '0.65rem',
      }}>
        <div style={{
          width: '32px',
          height: '32px',
          borderRadius: 'var(--radius-sm)',
          backgroundColor: isAdmin ? 'var(--teal-600)' : 'var(--primary-600)',
          color: '#ffffff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          {isAdmin ? <ShieldAlert size={18} /> : <Activity size={18} />}
        </div>
        <div>
          <span style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--text-primary)', display: 'block', lineHeight: 1.1 }}>
            MedDevice
          </span>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            {isAdmin ? 'Admin Portal' : 'Risk Monitor'}
          </span>
        </div>
      </div>

      {/* Navigation Links */}
      <nav style={{ flex: 1, padding: '1.25rem 1rem', display: 'flex', flexDirection: 'column' }}>
        {isAdmin ? (
          <>
            <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', padding: '0.5rem 1rem 0.25rem' }}>
              Administration
            </div>
            <NavLink to="/admin/dashboard" style={navItemStyle}>
              <LayoutDashboard size={18} />
              <span>Overview</span>
            </NavLink>
            <NavLink to="/admin/users" style={navItemStyle}>
              <Users size={18} />
              <span>Users</span>
            </NavLink>
            <NavLink to="/admin/predictions" style={navItemStyle}>
              <FileSpreadsheet size={18} />
              <span>Predictions</span>
            </NavLink>
            <NavLink to="/admin/logs" style={navItemStyle}>
              <ScrollText size={18} />
              <span>Audit Logs</span>
            </NavLink>
            <NavLink to="/admin/profile" style={navItemStyle}>
              <User size={18} />
              <span>Profile</span>
            </NavLink>
          </>
        ) : (
          <>
            <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', padding: '0.5rem 1rem 0.25rem' }}>
              Operations
            </div>
            <NavLink to="/dashboard" style={navItemStyle}>
              <LayoutDashboard size={18} />
              <span>Dashboard</span>
            </NavLink>
            <NavLink to="/assessment" style={navItemStyle}>
              <ShieldPlus size={18} />
              <span>New Risk Assessment</span>
            </NavLink>
            <NavLink to="/predictions" style={navItemStyle}>
              <History size={18} />
              <span>Prediction History</span>
            </NavLink>
            <NavLink to="/profile" style={navItemStyle}>
              <User size={18} />
              <span>Profile</span>
            </NavLink>
          </>
        )}
      </nav>

      {/* User Info & Logout Footer */}
      <div style={{
        padding: '1rem',
        borderTop: '1px solid var(--border-subtle)',
        backgroundColor: 'var(--bg-app)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
          <div style={{ minWidth: 0 }}>
            <p style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {user?.full_name || 'User'}
            </p>
            <span style={{
              display: 'inline-block',
              fontSize: '0.7rem',
              fontWeight: 700,
              padding: '0.15rem 0.4rem',
              borderRadius: '4px',
              backgroundColor: isAdmin ? 'var(--teal-50)' : 'var(--primary-50)',
              color: isAdmin ? 'var(--teal-700)' : 'var(--primary-700)',
              border: `1px solid ${isAdmin ? 'var(--teal-600)' : 'var(--primary-100)'}`,
            }}>
              {user?.role === 'BIOMEDICAL_ENGINEER' ? 'Biomedical Engineer' : user?.role === 'MAINTENANCE_TEAM' ? 'Maintenance Team' : 'Administrator'}
            </span>
          </div>
        </div>

        <button
          onClick={handleLogout}
          className="btn btn-secondary"
          style={{ width: '100%', fontSize: '0.8rem', padding: '0.45rem 0.75rem', gap: '0.4rem' }}
        >
          <LogOut size={15} />
          <span>Logout</span>
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
